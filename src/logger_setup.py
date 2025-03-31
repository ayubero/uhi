import logging.config
from omegaconf import OmegaConf

# Load the YAML config file
config = OmegaConf.load('config.yaml')

# Convert OmegaConf DictConfig to a regular dictionary
logging_config = OmegaConf.to_container(config.logging, resolve=True)

# Apply the logging configuration
logging.config.dictConfig(logging_config)

logger = logging.getLogger('logger')