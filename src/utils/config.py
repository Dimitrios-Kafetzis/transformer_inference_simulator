from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
import yaml
import json
import os
from pathlib import Path
import numpy as np
from ..environment import TopologyConfig, WorkloadType

@dataclass
class NetworkConfig:
    """Network topology configuration"""
    topology_type: str  # edge_cluster, distributed_edge, or hybrid_cloud_edge
    num_devices: int
    min_bandwidth: float
    max_bandwidth: float
    edge_probability: float = 0.3
    seed: Optional[int] = None

@dataclass
class ResourceConfig:
    """Resource distribution configuration"""
    memory_mu: float
    memory_sigma: float
    memory_min: float
    memory_max: float
    compute_mu: float
    compute_sigma: float
    compute_min: float
    compute_max: float
    seed: Optional[int] = None

@dataclass
class WorkloadConfig:
    """Workload generation configuration"""
    model_type: WorkloadType
    initial_sequence_lengths: List[int]
    generation_steps: List[int]
    precision_bytes: int = 4
    seed: Optional[int] = None

@dataclass
class AlgorithmConfig:
    """Algorithm configuration parameters"""
    migration_threshold: float = 0.9
    backtrack_limit: int = 100
    cache_placement_strategy: str = "colocated"
    enable_dynamic_adjustment: bool = True

@dataclass
class ExperimentConfig:
    """Experiment configuration"""
    name: str
    description: str
    num_runs: int = 1
    checkpoint_interval: int = 10
    time_limit: float = float('inf')
    metrics_output_dir: str = "results"
    save_intermediate: bool = False

@dataclass
class SimulationConfig:
    """Complete simulation configuration"""
    network: NetworkConfig
    resources: ResourceConfig
    workload: WorkloadConfig
    algorithm: AlgorithmConfig
    experiment: ExperimentConfig
    
    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'SimulationConfig':
        """Create configuration from dictionary"""
        return cls(
            network=NetworkConfig(**config_dict['network']),
            resources=ResourceConfig(**config_dict['resources']),
            workload=WorkloadConfig(
                model_type=WorkloadType[config_dict['workload']['model_type']],
                **{k: v for k, v in config_dict['workload'].items() 
                   if k != 'model_type'}
            ),
            algorithm=AlgorithmConfig(**config_dict['algorithm']),
            experiment=ExperimentConfig(**config_dict['experiment'])
        )
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        return {
            'network': {
                'topology_type': self.network.topology_type,
                'num_devices': self.network.num_devices,
                'min_bandwidth': self.network.min_bandwidth,
                'max_bandwidth': self.network.max_bandwidth,
                'edge_probability': self.network.edge_probability,
                'seed': self.network.seed
            },
            'resources': {
                'memory_mu': self.resources.memory_mu,
                'memory_sigma': self.resources.memory_sigma,
                'memory_min': self.resources.memory_min,
                'memory_max': self.resources.memory_max,
                'compute_mu': self.resources.compute_mu,
                'compute_sigma': self.resources.compute_sigma,
                'compute_min': self.resources.compute_min,
                'compute_max': self.resources.compute_max,
                'seed': self.resources.seed
            },
            'workload': {
                'model_type': self.workload.model_type.name,
                'initial_sequence_lengths': self.workload.initial_sequence_lengths,
                'generation_steps': self.workload.generation_steps,
                'precision_bytes': self.workload.precision_bytes,
                'seed': self.workload.seed
            },
            'algorithm': {
                'migration_threshold': self.algorithm.migration_threshold,
                'backtrack_limit': self.algorithm.backtrack_limit,
                'cache_placement_strategy': self.algorithm.cache_placement_strategy,
                'enable_dynamic_adjustment': self.algorithm.enable_dynamic_adjustment
            },
            'experiment': {
                'name': self.experiment.name,
                'description': self.experiment.description,
                'num_runs': self.experiment.num_runs,
                'checkpoint_interval': self.experiment.checkpoint_interval,
                'time_limit': self.experiment.time_limit,
                'metrics_output_dir': self.experiment.metrics_output_dir,
                'save_intermediate': self.experiment.save_intermediate
            }
        }

def create_default_config() -> SimulationConfig:
    """Create default configuration"""
    return SimulationConfig(
        network=NetworkConfig(
            topology_type="edge_cluster",
            num_devices=8,
            min_bandwidth=1.0,
            max_bandwidth=10.0
        ),
        resources=ResourceConfig(
            memory_mu=2.0,
            memory_sigma=0.5,
            memory_min=1.0,
            memory_max=16.0,
            compute_mu=5.0,
            compute_sigma=0.5,
            compute_min=1.0,
            compute_max=32.0
        ),
        workload=WorkloadConfig(
            model_type=WorkloadType.SMALL,
            initial_sequence_lengths=[128, 256, 512],
            generation_steps=[32, 64, 128]
        ),
        algorithm=AlgorithmConfig(),
        experiment=ExperimentConfig(
            name="default_experiment",
            description="Default experiment configuration"
        )
    )

def load_config(config_path: Union[str, Path]) -> SimulationConfig:
    """Load configuration from file"""
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(config_path, 'r') as f:
        if config_path.suffix == '.yaml':
            config_dict = yaml.safe_load(f)
        elif config_path.suffix == '.json':
            config_dict = json.load(f)
        else:
            raise ValueError("Configuration file must be .yaml or .json")
            
    return SimulationConfig.from_dict(config_dict)

def save_config(config: SimulationConfig, config_path: Union[str, Path]) -> None:
    """Save configuration to file"""
    config_path = Path(config_path)
    config_dict = config.to_dict()
    
    # Create directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        if config_path.suffix == '.yaml':
            yaml.safe_dump(config_dict, f, default_flow_style=False)
        elif config_path.suffix == '.json':
            json.dump(config_dict, f, indent=2)
        else:
            raise ValueError("Configuration file must be .yaml or .json")

def validate_config(config: SimulationConfig) -> bool:
    """Validate configuration parameters"""
    try:
        # Validate network configuration
        if config.network.num_devices <= 0:
            return False
        if config.network.min_bandwidth <= 0 or config.network.max_bandwidth <= 0:
            return False
        if config.network.min_bandwidth > config.network.max_bandwidth:
            return False
        if not 0 <= config.network.edge_probability <= 1:
            return False
            
        # Validate resource configuration
        if any(x <= 0 for x in [
            config.resources.memory_min,
            config.resources.memory_max,
            config.resources.compute_min,
            config.resources.compute_max
        ]):
            return False
        if config.resources.memory_min > config.resources.memory_max:
            return False
        if config.resources.compute_min > config.resources.compute_max:
            return False
            
        # Validate workload configuration
        if not config.workload.initial_sequence_lengths:
            return False
        if not config.workload.generation_steps:
            return False
        if any(x <= 0 for x in config.workload.initial_sequence_lengths):
            return False
        if any(x <= 0 for x in config.workload.generation_steps):
            return False
        if config.workload.precision_bytes <= 0:
            return False
            
        # Validate algorithm configuration
        if not 0 <= config.algorithm.migration_threshold <= 1:
            return False
        if config.algorithm.backtrack_limit <= 0:
            return False
            
        # Validate experiment configuration
        if config.experiment.num_runs <= 0:
            return False
        if config.experiment.checkpoint_interval <= 0:
            return False
        if config.experiment.time_limit <= 0:
            return False
            
        return True
        
    except Exception:
        return False

def merge_configs(base_config: SimulationConfig, 
                 override_config: Dict) -> SimulationConfig:
    """Merge base configuration with override values"""
    base_dict = base_config.to_dict()
    
    # Recursively update configuration
    def update_dict(d1: Dict, d2: Dict) -> Dict:
        for k, v in d2.items():
            if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
                d1[k] = update_dict(d1[k], v)
            else:
                d1[k] = v
        return d1
        
    merged_dict = update_dict(base_dict, override_config)
    return SimulationConfig.from_dict(merged_dict)