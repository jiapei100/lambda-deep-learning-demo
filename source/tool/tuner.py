import os
import random
import importlib

from source.tool import config_parser


CONVERT_STR2NUM = ["piecewise_lr_decay", "piecewise_boundaries"]


def forward_props(source_obj, target_obj):
  public_props = (
    name for name in dir(target_obj) if not name.startswith('_'))
  for props_name in public_props:
    if hasattr(source_obj, props_name):
      setattr(target_obj, props_name, getattr(source_obj, props_name))


def type_convert(v):
    """ convert value to int, float or str"""
    try:
        float(v)
        tp = 1 if v.count(".") == 0 else 2
    except ValueError:
        tp = -1
    if tp == 1:
      return int(v)
    elif tp == 2:
      return float(v)
    elif tp == -1:
      return v
    else:
      assert False, "Unknown type for hyper parameter: {}".format(tp)


def excute(config, runner_config, callback_config,
           inputter_config, modeler_config,
           inputter_module, modeler_module,
           runner_module,
           callback_names):

  augmenter = (None if not config.augmenter else
               importlib.import_module(
                "source.augmenter." + config.augmenter))

  net = getattr(importlib.import_module(
    "source.network." + config.network), "net")

  callbacks = []
  for name in callback_names:
    callback = importlib.import_module(
      "source.callback." + name).build(
      callback_config)
    callbacks.append(callback)

  inputter = inputter_module.build(
    inputter_config, augmenter)

  modeler = modeler_module.build(
    modeler_config, net)

  runner = runner_module.build(
    runner_config, inputter, modeler, callbacks)

  # Run application
  runner.run()


def train(config,
          runner_config,
          callback_config,
          inputter_config,
          modeler_config,
          inputter_module,
          modeler_module,
          runner_module):

  runner_config.mode = "train"
  callback_config.mode = "train"
  inputter_config.mode = "train"
  modeler_config.mode = "train"

  inputter_config.dataset_meta = \
      os.path.expanduser(config.train_dataset_meta)

  excute(config,
         runner_config,
         callback_config,
         inputter_config,
         modeler_config,
         inputter_module,
         modeler_module,
         runner_module,
         config.train_callbacks)


def eval(config,
         runner_config,
         callback_config,
         inputter_config,
         modeler_config,
         inputter_module,
         modeler_module,
         runner_module):

  runner_config.mode = "eval"
  callback_config.mode = "eval"
  inputter_config.mode = "eval"
  modeler_config.mode = "eval"

  inputter_config.epochs = 1

  # Optional: use a different split for evaluation
  # Should not use testing dataset
  inputter_config.dataset_meta = \
      os.path.expanduser(config.eval_dataset_meta)

  excute(config,
         runner_config,
         callback_config,
         inputter_config,
         modeler_config,
         inputter_module,
         modeler_module,
         runner_module,
         config.eval_callbacks)


def tune(config, runner_config, callback_config,
         inputter_config, modeler_config,
         inputter_module, modeler_module,
         runner_module):

  # Parse config file
  tune_config = config_parser.yaml_parse(config.tune_config_path)

  # Setup the tuning jobs
  num_trials = tune_config["num_trials"]

  dir_ori = os.path.join(callback_config.model_dir, "tune", "trial")
  t = 0
  while t < num_trials:
    dir_update = dir_ori

    # Update fixed params (epochs needs to be reset)
    for field in tune_config["fixedparams"].keys():
      if field in CONVERT_STR2NUM:
        setattr(config, field,
                list(map(float, tune_config["fixedparams"][field].split(","))))
      else:
        setattr(config, field, tune_config["fixedparams"][field])

    # Update hyper parameter
    for sample_type in tune_config["hyperparams"].keys():
      for field in tune_config["hyperparams"][sample_type].keys():
        if hasattr(config, field):

          if sample_type == "generate":
            values = list(
              map(float,
                  tune_config["hyperparams"][sample_type][field].split(",")))
            v = 10 ** random.uniform(values[0], values[1])
            setattr(config, field, v)
            dir_update = dir_update + "_" + field + "_" + "{0:.5f}".format(v)
          elif sample_type == "select":
            values = tune_config["hyperparams"][sample_type][field].split(",")
            v = type_convert(random.choice(values))
            setattr(config, field, v)
            dir_update = dir_update + "_" + field + "_" + str(v)

    
    if not os.path.isdir(dir_update):
      config.model_dir = dir_update

      forward_props(config, runner_config)
      forward_props(config, callback_config)
      forward_props(config, inputter_config)
      forward_props(config, modeler_config)

      train(config,
            runner_config,
            callback_config,
            inputter_config,
            modeler_config,
            inputter_module,
            modeler_module,
            runner_module)

      eval(config,
           runner_config,
           callback_config,
           inputter_config,
           modeler_config,
           inputter_module,
           modeler_module,
           runner_module)

    t = t + 1
