#!/usr/bin/env python3
"""Small PyTorch executor for Leien's offline Hm4Cpv1 OpenVINO IR.

The bundled OpenVINO CPU plugin cannot compile this legacy dynamic-shape model
on Apple Silicon.  Hm4Cpv1 only uses a small, stable set of operators, so this
module reads the original IR weights and evaluates the graph with PyTorch.
"""

from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import torch
import torch.nn.functional as F


_DTYPES = {
    "f32": (np.float32, torch.float32),
    "i32": (np.int32, torch.int32),
    "i64": (np.int64, torch.int64),
}


def _numbers(value, cast=int):
    if value is None or value == "":
        return ()
    return tuple(cast(part.strip()) for part in value.split(","))


class Hm4Cpv1TorchRuntime:
    """Evaluate the recovered Hm4Cpv1 IR without an OpenVINO dependency."""

    def __init__(self, xml_path: Path, weights_path: Path):
        self.xml_path = Path(xml_path)
        self.weights_path = Path(weights_path)
        if not self.xml_path.exists() or not self.weights_path.exists():
            raise FileNotFoundError(
                f"Hm4Cpv1 IR is incomplete: {self.xml_path}, {self.weights_path}"
            )

        root = ET.parse(self.xml_path).getroot()
        self.layers = {
            int(layer.attrib["id"]): layer for layer in root.findall("./layers/layer")
        }
        self.incoming = defaultdict(dict)
        for edge in root.findall("./edges/edge"):
            self.incoming[int(edge.attrib["to-layer"])][int(edge.attrib["to-port"])] = int(
                edge.attrib["from-layer"]
            )
        self.weights = self.weights_path.read_bytes()
        self.constants = {}
        self.result_id = next(
            layer_id
            for layer_id, layer in self.layers.items()
            if layer.attrib.get("type") == "Result"
        )

    def _constant(self, layer_id, layer):
        cached = self.constants.get(layer_id)
        if cached is not None:
            return cached
        data = layer.find("data").attrib
        element_type = data.get("element_type", "f32")
        numpy_dtype, torch_dtype = _DTYPES[element_type]
        offset = int(data.get("offset", 0))
        size = int(data.get("size", 0))
        shape = _numbers(data.get("shape"), int)
        array = np.frombuffer(self.weights[offset : offset + size], dtype=numpy_dtype).copy()
        if shape:
            array = array.reshape(shape)
        elif array.size == 1:
            array = array.reshape(())
        tensor = torch.from_numpy(array).to(dtype=torch_dtype)
        self.constants[layer_id] = tensor
        return tensor

    @staticmethod
    def _pad_spatial(value, pads_begin, pads_end, mode="constant", pad_value=0.0):
        if len(pads_begin) == 2:
            top, left = pads_begin
            bottom, right = pads_end
        else:
            top, left = pads_begin[-2:]
            bottom, right = pads_end[-2:]
        if not any((top, left, bottom, right)):
            return value
        return F.pad(value, (left, right, top, bottom), mode=mode, value=pad_value)

    def run(self, image_rgb, coarse_rgba):
        """Run one NCHW RGB/RGBA patch and return a NCHW refined RGBA array."""
        parameters = {
            "input": torch.as_tensor(image_rgb, dtype=torch.float32),
            "matting": torch.as_tensor(coarse_rgba, dtype=torch.float32),
        }
        cache = {}

        def evaluate(layer_id):
            if layer_id in cache:
                return cache[layer_id]
            layer = self.layers[layer_id]
            op_type = layer.attrib.get("type")
            name = layer.attrib.get("name", "")
            data_node = layer.find("data")
            attrs = data_node.attrib if data_node is not None else {}

            if op_type == "Parameter":
                value = parameters[name]
            elif op_type == "Const":
                value = self._constant(layer_id, layer)
            else:
                sources = self.incoming[layer_id]
                values = [evaluate(sources[port]) for port in sorted(sources)]
                if op_type == "Result":
                    value = values[0]
                elif op_type == "Concat":
                    value = torch.cat(values, dim=int(attrs.get("axis", 1)))
                elif op_type == "Add":
                    value = values[0] + values[1]
                elif op_type == "Multiply":
                    value = values[0] * values[1]
                elif op_type == "PReLU":
                    value = torch.where(values[0] >= 0, values[0], values[0] * values[1])
                elif op_type == "LeakyRelu":
                    value = F.leaky_relu(values[0], float(attrs.get("negative_slope", 0.2)))
                elif op_type == "ReLU":
                    value = F.relu(values[0])
                elif op_type == "Convolution":
                    stride = _numbers(attrs.get("strides", "1,1"))
                    dilation = _numbers(attrs.get("dilations", "1,1"))
                    begin = _numbers(attrs.get("pads_begin", "0,0"))
                    end = _numbers(attrs.get("pads_end", "0,0"))
                    source = self._pad_spatial(values[0], begin, end)
                    value = F.conv2d(source, values[1], stride=stride, dilation=dilation)
                elif op_type == "ConvolutionBackpropData":
                    stride = _numbers(attrs.get("strides", "1,1"))
                    dilation = _numbers(attrs.get("dilations", "1,1"))
                    padding = _numbers(attrs.get("pads_begin", "0,0"))
                    output_padding = _numbers(attrs.get("output_padding", "0,0"))
                    value = F.conv_transpose2d(
                        values[0],
                        values[1],
                        stride=stride,
                        padding=padding,
                        output_padding=output_padding,
                        dilation=dilation,
                    )
                elif op_type == "Pad":
                    pads_begin = tuple(int(v) for v in values[1].reshape(-1).tolist())
                    pads_end = tuple(int(v) for v in values[2].reshape(-1).tolist())
                    mode = attrs.get("pad_mode", "constant")
                    pad_value = float(values[3]) if len(values) > 3 else 0.0
                    value = self._pad_spatial(values[0], pads_begin, pads_end, mode, pad_value)
                elif op_type == "AvgPool":
                    kernel = _numbers(attrs.get("kernel", "2,2"))
                    stride = _numbers(attrs.get("strides", "1,1"))
                    padding = _numbers(attrs.get("pads_begin", "0,0"))
                    value = F.avg_pool2d(
                        values[0],
                        kernel_size=kernel,
                        stride=stride,
                        padding=padding,
                        count_include_pad=attrs.get("exclude-pad", "false") != "true",
                    )
                else:
                    raise RuntimeError(f"Unsupported Hm4Cpv1 IR op: {op_type} ({name})")

            cache[layer_id] = value
            return value

        with torch.inference_mode():
            output = evaluate(self.result_id)
        return output.detach().cpu().numpy()
