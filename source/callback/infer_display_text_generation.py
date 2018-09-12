"""
Copyright 2018 Lambda Labs. All Rights Reserved.
Licensed under
==========================================================================

"""
from __future__ import print_function

import numpy as np

import tensorflow as tf

from callback import Callback


def pick(prob):
    t = np.cumsum(prob)
    s = np.sum(prob)
    return(int(np.searchsorted(t, np.random.rand(1) * s)))


class InferDisplayTextGeneration(Callback):
  def __init__(self, args):
    super(InferDisplayTextGeneration, self).__init__(args)
    self.input = ""
    self.output = ""

  def before_run(self, sess, saver):
    self.graph = tf.get_default_graph()

  def after_run(self, sess, saver, summary_writer):
    print(self.input)
    print('-------------------------------------------------')
    print(self.output)

  def before_step(self, sess):
    pass

  def after_step(self, sess, outputs_dict,
                 saver, summary_writer, feed_dict=None):
    chars = outputs_dict["chars"]
    for i, p in zip(outputs_dict["inputs"], outputs_dict["probabilities"]):
      self.input += chars[i[0]]

      pick_id = pick(p)

      self.output += chars[pick_id]

      # Get the placeholder for inputs
      inputs_place_holder = self.graph.get_tensor_by_name("inputs:0")

      # Python passes dictionary by reference
      feed_dict[inputs_place_holder] = np.array([[pick_id]], dtype=np.int32)


def build(args):
  return InferDisplayTextGeneration(args)