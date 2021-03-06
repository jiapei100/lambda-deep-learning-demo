"""
Copyright 2018 Lambda Labs. All Rights Reserved.
Licensed under
==========================================================================

"""
from __future__ import print_function
import six
from collections import Counter
import operator
import numpy as np

import tensorflow as tf

from inputter import Inputter


class TextGenerationTXTInputter(Inputter):
  def __init__(self, config, augmenter):
    super(TextGenerationTXTInputter, self).__init__(config, augmenter)

    if self.config.mode == "train":
      self.num_samples = 100000
      self.seq_length = 50
    elif self.config.mode == "infer":
      self.num_samples = 1000
      self.seq_length = 1
    elif self.config.mode == "eval":
      self.num_samples = 10000
      self.seq_length = 50

    self.vocab_size = None

    self.initial_seq()

  def initial_seq(self):

    with open(self.config.dataset_meta, 'rb') as f:
      data = f.read()
    if six.PY2:
      data = bytearray(data)
    data = [chr(c) for c in data if c < 128]

    counter = Counter(data)
    char_cnt = sorted(counter.items(),
                      key=operator.itemgetter(1), reverse=True)
    self.chars = [x[0] for x in char_cnt]
    self.vocab_size = len(self.chars)
    self.char2idx = {c: i for i, c in enumerate(self.chars)}
    self.whole_seq = np.array([self.char2idx[c] for c in data], dtype='int32')
    print("char2idx: ")
    print(self.char2idx)

  def create_nonreplicated_fn(self):
    batch_size = (self.config.batch_size_per_gpu *
                  self.config.gpu_count)
    max_step = (self.get_num_samples() * self.config.epochs // batch_size)
    tf.constant(max_step, name="max_step")

  def get_num_samples(self):
    return self.num_samples

  def get_vocab_size(self):
    return self.vocab_size

  def get_chars(self):
    return self.chars

  def get_seq_length(self):
    return self.seq_length

  def get_samples_fn(self):
    random_starts = np.random.randint(
      0,
      self.whole_seq.shape[0] - self.seq_length - 1,
      (self.num_samples,))

    for st in random_starts:
        seq = self.whole_seq[st:st + self.seq_length + 1]
        yield seq[:-1], seq[1:]

  def parse_fn(self, inputs, outputs):
    """Parse a single input sample
    """
    inputs.set_shape([self.seq_length])
    outputs.set_shape([self.seq_length])

    return (inputs, outputs)

  def input_fn(self, test_samples=[]):
    batch_size = (self.config.batch_size_per_gpu *
                  self.config.gpu_count)
    if self.config.mode == "train" or self.config.mode == "eval":

      dataset = tf.data.Dataset.from_generator(
        generator=lambda: self.get_samples_fn(),
        output_types=(tf.int32, tf.int32))

      dataset = dataset.repeat(self.config.epochs)

      dataset = dataset.map(
        lambda inputs, outputs: self.parse_fn(inputs, outputs),
        num_parallel_calls=4)

      dataset = dataset.apply(
          tf.contrib.data.batch_and_drop_remainder(batch_size))

      dataset = dataset.prefetch(2)

      iterator = dataset.make_one_shot_iterator()
      return iterator.get_next()
    else:
      return (tf.zeros([batch_size, self.seq_length], tf.int32),
              tf.zeros([batch_size, self.seq_length], tf.int32))


def build(config, augmenter):
  return TextGenerationTXTInputter(config, augmenter)
