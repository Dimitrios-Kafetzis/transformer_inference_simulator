# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 Dimitrios Kafetzis
#
# This file is part of the Transformer Inference Simulator project.
# Licensed under the MIT License; you may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#   https://opensource.org/licenses/MIT
#
# Author:  Dimitrios Kafetzis (dimitrioskafetzis@gmail.com)
# File:    src/utils/visualization.py
# Description:
#   Implements the VisualizationManager and functions to generate plots
#   and performance reports for simulation metrics and network topologies.
#
# ---------------------------------------------------------------------------

"""
Contains classes and methods for plotting resource utilization, communication
patterns, network topologies, and general performance metrics of distributed
Transformer inference. Also provides facilities for generating JSON-based
reports from simulation data.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import json
from datetime import datetime

class VisualizationManager:
    """Manages creation and saving of visualization plots"""
    
    def __init__(
        self,
        output_dir: Union[str, Path],
        style: str = 'seaborn-whitegrid'
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        plt.style.use(style)
        
    def save_plot(
        self,
        fig: plt.Figure,
        name: str,
        formats: List[str] = ['png', 'pdf']
    ) -> None:
        """Save plot in multiple formats"""
        for fmt in formats:
            fig.savefig(
                self.output_dir / f"{name}.{fmt}",
                bbox_inches='tight',
                dpi=300
            )
            
    def plot_resource_utilization(
        self,
        metrics_data: pd.DataFrame,
        device_ids: List[str]
    ) -> plt.Figure:
        """Plot resource utilization over time for each device"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Memory utilization
        for device_id in device_ids:
            device_data = metrics_data[metrics_data['device_id'] == device_id]
            ax1.plot(
                device_data['step'],
                device_data['memory_utilization'],
                label=f'Device {device_id}'
            )
            
        ax1.set_xlabel('Generation Step')
        ax1.set_ylabel('Memory Utilization (%)')
        ax1.set_title('Memory Utilization Over Time')
        ax1.legend()
        ax1.grid(True)
        
        # Compute utilization
        for device_id in device_ids:
            device_data = metrics_data[metrics_data['device_id'] == device_id]
            ax2.plot(
                device_data['step'],
                device_data['compute_utilization'],
                label=f'Device {device_id}'
            )
            
        ax2.set_xlabel('Generation Step')
        ax2.set_ylabel('Compute Utilization (%)')
        ax2.set_title('Compute Utilization Over Time')
        ax2.legend()
        ax2.grid(True)
        
        fig.tight_layout()
        return fig
        
    def plot_latency_comparison(
        self,
        algorithms: List[str],
        latencies: Dict[str, List[float]],
        workload_types: List[str]
    ) -> plt.Figure:
        """Plot latency comparison between algorithms"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = np.arange(len(workload_types))
        width = 0.8 / len(algorithms)
        
        for i, algo in enumerate(algorithms):
            positions = x + i * width - (len(algorithms) - 1) * width / 2
            ax.bar(
                positions,
                [latencies[algo][j] for j in range(len(workload_types))],
                width,
                label=algo
            )
            
        ax.set_xlabel('Workload Type')
        ax.set_ylabel('Average Latency (ms)')
        ax.set_title('Latency Comparison Across Algorithms')
        ax.set_xticks(x)
        ax.set_xticklabels(workload_types)
        ax.legend()
        ax.grid(True, axis='y')
        
        return fig
        
    def plot_network_topology(
        self,
        graph: nx.Graph,
        node_colors: Dict[str, str],
        edge_weights: Dict[Tuple[str, str], float]
    ) -> plt.Figure:
        """Plot network topology with resource information"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create layout
        pos = nx.spring_layout(graph)
        
        # Draw nodes
        nx.draw_networkx_nodes(
            graph,
            pos,
            node_color=[node_colors[node] for node in graph.nodes()],
            node_size=1000,
            alpha=0.6
        )
        
        # Draw edges with width proportional to bandwidth
        edges = list(graph.edges())
        edge_widths = [edge_weights.get((u, v), 1.0) for u, v in edges]
        nx.draw_networkx_edges(
            graph,
            pos,
            width=edge_widths,
            alpha=0.5
        )
        
        # Add labels
        nx.draw_networkx_labels(graph, pos)
        
        ax.set_title("Network Topology")
        ax.axis('off')
        
        return fig
        
    def plot_workload_statistics(
        self,
        workload_data: pd.DataFrame
    ) -> plt.Figure:
        """Plot workload statistics and performance metrics"""
        fig = plt.figure(figsize=(15, 10))
        gs = fig.add_gridspec(2, 2)
        
        # Sequence length distribution
        ax1 = fig.add_subplot(gs[0, 0])
        sns.boxplot(
            data=workload_data,
            x='model_type',
            y='sequence_length',
            ax=ax1
        )
        ax1.set_title('Sequence Length Distribution')
        ax1.set_ylabel('Sequence Length')
        
        # Generation steps distribution
        ax2 = fig.add_subplot(gs[0, 1])
        sns.boxplot(
            data=workload_data,
            x='model_type',
            y='generation_steps',
            ax=ax2
        )
        ax2.set_title('Generation Steps Distribution')
        ax2.set_ylabel('Number of Steps')
        
        # Memory requirements
        ax3 = fig.add_subplot(gs[1, 0])
        sns.barplot(
            data=workload_data,
            x='model_type',
            y='memory_requirement',
            ax=ax3
        )
        ax3.set_title('Memory Requirements')
        ax3.set_ylabel('Memory (GB)')
        
        # Compute requirements
        ax4 = fig.add_subplot(gs[1, 1])
        sns.barplot(
            data=workload_data,
            x='model_type',
            y='compute_requirement',
            ax=ax4
        )
        ax4.set_title('Compute Requirements')
        ax4.set_ylabel('Compute (GFLOPS)')
        
        fig.tight_layout()
        return fig
        
    def plot_communication_patterns(
        self,
        comm_data: pd.DataFrame
    ) -> plt.Figure:
        """Plot communication patterns and overhead"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Data transfer volume
        sns.barplot(
            data=comm_data,
            x='source_device',
            y='data_volume',
            ax=ax1
        )
        ax1.set_title('Data Transfer Volume by Device')
        ax1.set_xlabel('Source Device')
        ax1.set_ylabel('Data Volume (GB)')
        plt.xticks(rotation=45)
        
        # Communication latency
        sns.boxplot(
            data=comm_data,
            x='source_device',
            y='transfer_time',
            ax=ax2
        )
        ax2.set_title('Communication Latency Distribution')
        ax2.set_xlabel('Source Device')
        ax2.set_ylabel('Transfer Time (ms)')
        plt.xticks(rotation=45)
        
        fig.tight_layout()
        return fig
        
    def plot_migration_analysis(
        self,
        migration_data: pd.DataFrame
    ) -> plt.Figure:
        """Plot migration patterns and costs"""
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
        
        # Migration frequency
        sns.countplot(
            data=migration_data,
            x='step',
            ax=ax1
        )
        ax1.set_title('Migration Frequency Over Time')
        ax1.set_xlabel('Generation Step')
        ax1.set_ylabel('Number of Migrations')
        
        # Migration costs
        sns.boxplot(
            data=migration_data,
            x='component_type',
            y='migration_cost',
            ax=ax2
        )
        ax2.set_title('Migration Cost by Component Type')
        ax2.set_xlabel('Component Type')
        ax2.set_ylabel('Migration Cost (ms)')
        
        # Migration patterns
        migration_matrix = pd.crosstab(
            migration_data['source_device'],
            migration_data['target_device']
        )
        sns.heatmap(
            migration_matrix,
            annot=True,
            fmt='d',
            ax=ax3
        )
        ax3.set_title('Migration Patterns Between Devices')
        
        fig.tight_layout()
        return fig
        
    def create_performance_report(
        self,
        metrics_data,
        output_file: Union[str, Path]
    ) -> None:
        """
        Create a comprehensive performance report from metrics_data.
    
        This version checks for columns before trying to compute stats to avoid KeyError.
        If columns are missing, we provide safe defaults (e.g., 0.0).
        """
        # If your code expects a pandas DataFrame, ensure metrics_data is indeed a DataFrame here.
        # If metrics_data is a dict, convert it or adapt accordingly.
        import pandas as pd
        from datetime import datetime
        import json
    
        # If the user passes something not a DataFrame, you can try:
        # if isinstance(metrics_data, dict):
        #     metrics_data = pd.DataFrame([metrics_data])  # or handle differently
    
        # Safe retrieval helpers
        def safe_max(df, col):
            return float(df[col].max()) if col in df.columns and not df.empty else 0.0
    
        def safe_mean(df, col):
            return float(df[col].mean()) if col in df.columns and not df.empty else 0.0
    
        def safe_sum(df, col):
            return float(df[col].sum()) if col in df.columns and not df.empty else 0.0
    
        # For event filtering
        def safe_filter(df, condition):
            if not df.empty and "event_type" in df.columns:
                return df[condition]
            return pd.DataFrame()
    
        # Build your summary statistics
        total_runtime = safe_max(metrics_data, "step")
        average_latency = safe_mean(metrics_data, "latency")
        latency_std = 0.0
        if "latency" in metrics_data.columns and not metrics_data.empty:
            latency_std = float(metrics_data["latency"].std())
    
        peak_mem_util = safe_max(metrics_data, "memory_utilization")
        peak_comp_util = safe_max(metrics_data, "compute_utilization")
    
        # If you track data transfers as a separate column
        total_data_transferred = safe_sum(metrics_data, "data_transferred")
    
        # Similarly for transfer_time
        avg_transfer_time = safe_mean(metrics_data, "transfer_time")
    
        # Migrations
        migration_df = safe_filter(metrics_data, (metrics_data["event_type"] == "migration"))
        total_migrations = len(migration_df)
        average_migration_cost = safe_mean(migration_df, "migration_cost")
    
        # Construct the final report dictionary
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary_statistics": {
                "total_runtime": total_runtime,
                "average_latency": average_latency,
                "latency_std": latency_std,
                "peak_memory_utilization": peak_mem_util,
                "peak_compute_utilization": peak_comp_util
            },
            "resource_utilization": {
                # Example: group by device_id if present
                # If you don't have device_id, skip or adapt
                "average_memory_utilization": {},
                "average_compute_utilization": {}
            },
            "communication_statistics": {
                "total_data_transferred": total_data_transferred,
                "average_transfer_time": avg_transfer_time
            },
            "migration_statistics": {
                "total_migrations": total_migrations,
                "average_migration_cost": average_migration_cost
            }
        }
    
        # Optionally, fill in resource_utilization grouped by device
        if "device_id" in metrics_data.columns:
            mem_group = metrics_data.groupby("device_id")["memory_utilization"].mean() \
                if "memory_utilization" in metrics_data.columns else pd.Series()
            comp_group = metrics_data.groupby("device_id")["compute_utilization"].mean() \
                if "compute_utilization" in metrics_data.columns else pd.Series()
            report["resource_utilization"]["average_memory_utilization"] = mem_group.to_dict()
            report["resource_utilization"]["average_compute_utilization"] = comp_group.to_dict()
    
        # Save the report as JSON
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

            
def plot_all_metrics(
    metrics_dir: Union[str, Path],
    output_dir: Union[str, Path]
) -> None:
    """Generate all plots for a simulation run"""
    viz = VisualizationManager(output_dir)
    
    # Load metrics data
    metrics_data = pd.read_json(
        Path(metrics_dir) / 'metrics.jsonl',
        lines=True
    )
    
    # Create all plots
    device_ids = metrics_data['device_id'].unique()
    
    # Resource utilization
    fig = viz.plot_resource_utilization(metrics_data, device_ids)
    viz.save_plot(fig, 'resource_utilization')
    plt.close(fig)
    
    # Communication patterns
    comm_data = metrics_data[metrics_data['event_type'] == 'communication']
    fig = viz.plot_communication_patterns(comm_data)
    viz.save_plot(fig, 'communication_patterns')
    plt.close(fig)
    
    # Migration analysis
    migration_data = metrics_data[metrics_data['event_type'] == 'migration']
    fig = viz.plot_migration_analysis(migration_data)
    viz.save_plot(fig, 'migration_analysis')
    plt.close(fig)
    
    # Create performance report
    viz.create_performance_report(
        metrics_data,
        output_dir / 'performance_report.json'
    )