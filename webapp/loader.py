import collections
import codecs
import os

from bert import tokenization
from webapp.text_model import *
import numpy as np


class InputExample(object):

    def __init__(self, guid, text_a, text_b=None, label=None):
        """
        构造bert模型样本的类
        Args:
          guid: 样本的编码，表示第几条数据，不是模型要输入的对应参数；
          text_a: 第一个序列文本，对应我们数据集要分类的文本；
          text_b: 第二个序列文本，是bert模型在sequence pair 任务要输入的文本，在我们这个场景不需要，设置为None;
          label: 文本标签
        """
        self.guid = guid
        self.text_a = text_a
        self.text_b = text_b
        self.label = label


class TextProcessor(object):
    """按照InputExample类形式载入对应的数据集"""

    """load train examples"""

    def get_train_examples(self, data_dir):
        return self._create_examples(
            self._read_file(os.path.join(data_dir, "train.tsv")), "train")

    """load dev examples"""

    def get_dev_examples(self, data_dir):
        return self._create_examples(
            self._read_file(os.path.join(data_dir, "dev.tsv")), "dev")

    """load test examples"""

    def get_test_examples(self, data_dir):
        return self._create_examples(
            self._read_file(os.path.join(data_dir, "test.tsv")), "test")

    """load pre examples"""

    def get_single_pre_example(self, data_dir):
        return self._create_examples(
            self._read_file(os.path.join(data_dir, "pre_test.tsv")), "test")

    """set labels"""

    def get_labels(self):
        return label_static

    """read file"""

    def _read_file(self, input_file):
        with codecs.open(input_file, "r", encoding='utf-8') as f:
            lines = []
            for line in f.readlines():
                try:
                    line = line.split('\t')
                    assert len(line) == 2
                    lines.append(line)
                except:
                    pass
            np.random.shuffle(lines)
            return lines

    """create examples for the data set """

    def _create_examples(self, lines, set_type):
        examples = []
        for (i, line) in enumerate(lines):
            guid = "%s-%s" % (set_type, i)
            text_a = tokenization.convert_to_unicode(line[1])
            label = tokenization.convert_to_unicode(line[0])
            examples.append(
                InputExample(guid=guid, text_a=text_a, text_b=None, label=label))
        return examples


def convert_examples_to_features(examples, label_list, max_seq_length, tokenizer, cmd_infer=False):
    """
    将所有的InputExamples样本（在网页访问时返回一个测试样本）数据转化成模型要输入的token形式，
    最后输出bert模型需要的四个变量，这四个变量打包存储在字典里，最终成为数组返回：
    input_ids：就是text_a(分类文本)在词库对应的token，按字符级；
    input_mask：bert模型mask训练的标记，都为1；
    segment_ids：句子标记，此场景只有text_a,都为0；
    label_ids：文本标签对应的token，不是one_hot的形式；
    cmd_infer: 在命令行推测模式时，cmd_infer为真可避免抛出定义的错误。因为，在命令行推测时，
               ..convert_examples_to_features()内部的label_id值一直是None类型。
    """
    label_map = {}
    for (i, label) in enumerate(label_list):
        label_map[label] = i

    input_data = []
    for (ex_index, example) in enumerate(examples):
        tokens_a = tokenizer.tokenize(example.text_a)
        if ex_index % 10000 == 0:
            tf.logging.info("Writing example %d of %d" % (ex_index, len(examples)))

        if len(tokens_a) > max_seq_length - 2:
            tokens_a = tokens_a[0:(max_seq_length - 2)]

        tokens = []
        segment_ids = []
        tokens.append("[CLS]")
        segment_ids.append(0)
        for token in tokens_a:
            tokens.append(token)
            segment_ids.append(0)
        tokens.append("[SEP]")
        segment_ids.append(0)
        input_ids = tokenizer.convert_tokens_to_ids(tokens)

        input_mask = [1] * len(input_ids)

        while len(input_ids) < max_seq_length:
            input_ids.append(0)
            input_mask.append(0)
            segment_ids.append(0)
        assert len(input_ids) == max_seq_length
        assert len(input_mask) == max_seq_length
        assert len(segment_ids) == max_seq_length

        try:
            label_id = label_map[example.label]
        except:
            label_id = None
            if cmd_infer is False:
                raise ValueError("语料库标签名或模型配置文件(text_model.py)中的标签名有错误，请检查是否一致！")
        if ex_index < 3:
            tf.logging.info("*** Example ***")
            tf.logging.info("guid: %s" % (example.guid))
            tf.logging.info("tokens: %s" % " ".join([tokenization.printable_text(x) for x in tokens]))
            tf.logging.info("input_ids: %s" % " ".join([str(x) for x in input_ids]))
            tf.logging.info("input_mask: %s" % " ".join([str(x) for x in input_mask]))
            tf.logging.info("segment_ids: %s" % " ".join([str(x) for x in segment_ids]))
            tf.logging.info("label: {} (id = {})".format(example.label, label_id))

        features = collections.OrderedDict()
        features["input_ids"] = input_ids
        features["input_mask"] = input_mask
        features["segment_ids"] = segment_ids
        features["label_ids"] = label_id
        input_data.append(features)

    return input_data


def batch_iter(input_data, batch_size):
    """
    将样本的四个tokens形式的变量批量的输入给模型；
    """
    batch_ids, batch_mask, batch_segment, batch_label = [], [], [], []
    for features in input_data:
        if len(batch_ids) == batch_size:
            yield batch_ids, batch_mask, batch_segment, batch_label
            batch_ids, batch_mask, batch_segment, batch_label = [], [], [], []

        batch_ids.append(features['input_ids'])
        batch_mask.append(features['input_mask'])
        batch_segment.append(features['segment_ids'])
        batch_label.append(features['label_ids'])

    if len(batch_ids) != 0:
        yield batch_ids, batch_mask, batch_segment, batch_label
