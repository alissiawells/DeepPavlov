# Copyright 2017 Neural Networks and Deep Learning lab, MIPT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from logging import getLogger
import random
import numpy as np
from overrides import overrides

import torch
import torchtext
import torchtext.datasets as torch_texts
from torch.utils.data.dataset import random_split

from deeppavlov.core.common.registry import register
from deeppavlov.core.data.dataset_reader import DatasetReader

log = getLogger(__name__)


def _init_fn():
    np.random.seed(12)
    torch.manual_seed(12)
    torch.cuda.manual_seed(12)


@register("torchtext_classification_data_reader")
class TorchtextClassificationDataReader(DatasetReader):
    """Class initializes datasets as an attribute of `torchtext.datasets`.
    Raw texts and string labels are re-assigned to common deeppavlov format of data which will be given to iterator.
    """
    @overrides
    def read(self, data_path: str, dataset_title: str,
             splits=["train", "valid", "test"], valid_portion=None,
             split_seed=42, *args, **kwargs) -> dict:

        if hasattr(torch_texts, dataset_title) and callable(getattr(torch_texts, dataset_title)):
            log.info(f"Dataset {dataset_title} is used as an attribute of `torchtext.datasets`.")
            _text = torchtext.data.RawField()
            _label = torchtext.data.RawField()
            data_splits = getattr(torch_texts, dataset_title).splits(_text, _label, root=data_path)
            assert len(data_splits) == len(splits)
            data_splits = {data_field: data_splits[i] for i, data_field in enumerate(splits)}

            if "valid" not in splits and valid_portion is not None:
                log.info("Valid not in `splits` and `valid_portion` is given. Split `train` to `train` and `valid`")
                data_splits["train"], data_splits["valid"] = data_splits["train"].split(
                    1 - valid_portion, random_state=random.seed(split_seed))
        else:
            raise NotImplementedError(f"Dataset {dataset_title} was not found.")

        data = {}
        for data_field in data_splits:
            data[data_field] = []
            for sample in data_splits[data_field].examples:
                data[data_field].append((vars(sample)["text"], vars(sample)["label"]))
            log.info(f"For field {data_field} found {len(data[data_field])} samples.")
        return data
