"""
Performance Monitor Event Formatter: GUI display formatting for performance monitoring events.

This module provides specialized formatting for performance monitor events, converting raw
performance metric dictionaries into various GUI-friendly formats while maintaining
complete separation from the raw data storage layer.

Key Features:
- Human-readable performance metric summaries
- Threshold status classification and alerts
- Chart-friendly data formatting
- Performance trend analysis
"""

from typing import Dict, List, Any, Union
from .base_formatter import EventFormatter


class PerformanceMonitorEventFormatter(EventFormatter):
    """
    Formatter for performance monitor events from the simulation.
    
    Handles conversion of raw performance monitor dictionaries (from RawDataObserver) 
    into GUI-friendly formats for display, analysis, and performance tracking.
    
    Raw Performance Monitor Event Schema:
    {
        'type': 'performance_monitor',
        'step': int,
        'metric_name': str,
        'metric_value': float,
        'threshold_exceeded': bool,
        'details': str  # Additional context
    }
    """
    
    # Metric display mappings
    METRIC_DISPLAY_NAMES = {
        'step_time': 'Step Time',
        'memory_usage': 'Memory Usage',
        'event_count': 'Event Count',
        'fps': 'Frames Per Second',
        'trade_rate': 'Trade Rate',
        'collection_rate': 'Collection Rate',
        'mode_change_rate': 'Mode Change Rate',
        'agent_count': 'Agent Count',
        'resource_density': 'Resource Density',
        'cpu_usage': 'CPU Usage',
        'render_time': 'Render Time',
        'update_time': 'Update Time'
    }
    
    # Metric units for display
    METRIC_UNITS = {
        'step_time': 'ms',
        'memory_usage': 'MB',
        'event_count': 'events',
        'fps': 'fps',
        'trade_rate': 'trades/sec',
        'collection_rate': 'collections/sec',
        'mode_change_rate': 'changes/sec',
        'agent_count': 'agents',
        'resource_density': '%',
        'cpu_usage': '%',
        'render_time': 'ms',
        'update_time': 'ms'
    }
    
    def to_display_text(self, raw_event: Dict[str, Any]) -> str:
        """Convert raw performance event to human-readable display text.
        
        Args:
            raw_event: Raw performance monitor dictionary
            
        Returns:
            Human-readable performance summary string
        """
        try:
            step = raw_event.get('step', -1)
            metric_name = raw_event.get('metric_name', 'unknown')
            metric_value = raw_event.get('metric_value', 0.0)
            threshold_exceeded = raw_event.get('threshold_exceeded', False)
            
            # Get display name and unit
            display_name = self.METRIC_DISPLAY_NAMES.get(metric_name, metric_name.title())
            unit = self.METRIC_UNITS.get(metric_name, '')
            
            # Format value based on metric type
            formatted_value = self._format_metric_value(metric_name, metric_value)
            
            # Create base message
            if unit:
                base_msg = f"{display_name}: {formatted_value} {unit}"
            else:
                base_msg = f"{display_name}: {formatted_value}"
            
            # Add threshold warning if exceeded
            if threshold_exceeded:
                return f"⚠️  {base_msg} (THRESHOLD EXCEEDED)"
            else:
                return f"📊 {base_msg}"
                
        except Exception as e:
            return f"❌ Performance Monitor Error (Step {raw_event.get('step', '?')}): {str(e)}"
    
    def to_analysis_data(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw performance event to analysis-friendly structure.
        
        Args:
            raw_event: Raw performance monitor dictionary
            
        Returns:
            Dictionary with analysis-friendly structure and computed fields
        """
        try:
            step = raw_event.get('step', -1)
            metric_name = raw_event.get('metric_name', 'unknown')
            metric_value = raw_event.get('metric_value', 0.0)
            threshold_exceeded = raw_event.get('threshold_exceeded', False)
            details = raw_event.get('details', '')
            
            # Classify metric performance level
            performance_level = self._classify_performance_level(metric_name, metric_value, threshold_exceeded)
            
            # Get metric category
            metric_category = self._get_metric_category(metric_name)
            
            # Calculate normalized value (0-1 scale)
            normalized_value = self._normalize_metric_value(metric_name, metric_value)
            
            return {
                'step': step,
                'metric_name': metric_name,
                'metric_display_name': self.METRIC_DISPLAY_NAMES.get(metric_name, metric_name.title()),
                'metric_value': metric_value,
                'formatted_value': self._format_metric_value(metric_name, metric_value),
                'unit': self.METRIC_UNITS.get(metric_name, ''),
                'threshold_exceeded': threshold_exceeded,
                'performance_level': performance_level,  # 'excellent', 'good', 'warning', 'critical'
                'metric_category': metric_category,  # 'performance', 'memory', 'throughput', 'system'
                'normalized_value': normalized_value,  # 0.0-1.0 scale for charting
                'has_details': bool(details.strip()),
                'details': details,
                'timestamp': step  # For time series analysis
            }
            
        except Exception as e:
            return {
                'step': raw_event.get('step', -1),
                'error': f"Analysis error: {str(e)}",
                'metric_name': raw_event.get('metric_name', 'unknown'),
                'metric_value': raw_event.get('metric_value', 0.0),
                'performance_level': 'error'
            }
    
    def to_table_row(self, raw_event: Dict[str, Any]) -> List[Union[str, int, float]]:
        """Convert raw performance event to table row format.
        
        Args:
            raw_event: Raw performance monitor dictionary
            
        Returns:
            List of values for table display: [Step, Metric, Value, Status, Details]
        """
        try:
            step = raw_event.get('step', -1)
            metric_name = raw_event.get('metric_name', 'unknown')
            metric_value = raw_event.get('metric_value', 0.0)
            threshold_exceeded = raw_event.get('threshold_exceeded', False)
            details = raw_event.get('details', '')
            
            # Get display name
            display_name = self.METRIC_DISPLAY_NAMES.get(metric_name, metric_name.title())
            
            # Format value with unit
            formatted_value = self._format_metric_value(metric_name, metric_value)
            unit = self.METRIC_UNITS.get(metric_name, '')
            value_with_unit = f"{formatted_value} {unit}".strip()
            
            # Status
            status = "THRESHOLD EXCEEDED" if threshold_exceeded else "Normal"
            
            # Truncate details for table display
            details_short = details[:50] + "..." if len(details) > 50 else details
            
            return [step, display_name, value_with_unit, status, details_short]
            
        except Exception as e:
            return [raw_event.get('step', -1), 'Error', str(e), 'Error', '']
    
    def to_detailed_view(self, raw_event: Dict[str, Any]) -> Dict[str, str]:
        """Convert raw performance event to detailed view format.
        
        Args:
            raw_event: Raw performance monitor dictionary
            
        Returns:
            Dictionary with detailed, structured information
        """
        try:
            analysis_data = self.to_analysis_data(raw_event)
            
            details_dict = {
                'Step': str(analysis_data['step']),
                'Metric Name': analysis_data['metric_display_name'],
                'Value': f"{analysis_data['formatted_value']} {analysis_data['unit']}".strip(),
                'Performance Level': analysis_data['performance_level'].title(),
                'Category': analysis_data['metric_category'].title(),
                'Threshold Status': 'Exceeded' if analysis_data['threshold_exceeded'] else 'Normal',
                'Normalized Value': f"{analysis_data['normalized_value']:.3f}"
            }
            
            if analysis_data['has_details']:
                details_dict['Additional Details'] = analysis_data['details']
            
            return details_dict
            
        except Exception as e:
            return {'Error': f"Detailed view error: {str(e)}"}
    
    # ============================================================================
    # SPECIALIZED PERFORMANCE MONITOR METHODS
    # ============================================================================
    
    def format_threshold_status(self, raw_event: Dict[str, Any]) -> Dict[str, str]:
        """Format threshold status information with severity levels.
        
        Args:
            raw_event: Raw performance monitor dictionary
            
        Returns:
            Dictionary with threshold status and formatting information
        """
        try:
            metric_name = raw_event.get('metric_name', 'unknown')
            metric_value = raw_event.get('metric_value', 0.0)
            threshold_exceeded = raw_event.get('threshold_exceeded', False)
            
            if threshold_exceeded:
                severity = self._get_threshold_severity(metric_name, metric_value)
                return {
                    'status': 'exceeded',
                    'severity': severity,  # 'warning', 'critical'
                    'css_class': f'threshold-{severity}',
                    'icon': '⚠️' if severity == 'warning' else '🚨',
                    'message': f"{self.METRIC_DISPLAY_NAMES.get(metric_name, metric_name)} threshold {severity}"
                }
            else:
                return {
                    'status': 'normal',
                    'severity': 'normal',
                    'css_class': 'threshold-normal',
                    'icon': '✅',
                    'message': 'Within normal range'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'severity': 'error',
                'css_class': 'threshold-error',
                'icon': '❌',
                'message': f'Status error: {str(e)}'
            }
    
    def to_chart_data(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw performance event to chart-friendly format.
        
        Args:
            raw_event: Raw performance monitor dictionary
            
        Returns:
            Dictionary optimized for charting libraries
        """
        try:
            step = raw_event.get('step', -1)
            metric_name = raw_event.get('metric_name', 'unknown')
            metric_value = raw_event.get('metric_value', 0.0)
            threshold_exceeded = raw_event.get('threshold_exceeded', False)
            
            # Normalize value for consistent charting
            normalized_value = self._normalize_metric_value(metric_name, metric_value)
            
            return {
                'x': step,  # X-axis (time/step)
                'y': metric_value,  # Y-axis (raw value)
                'normalized_y': normalized_value,  # Normalized Y-axis (0-1)
                'series': metric_name,  # Data series name
                'category': self._get_metric_category(metric_name),
                'threshold_exceeded': threshold_exceeded,
                'color': self._get_metric_color(metric_name, threshold_exceeded),
                'tooltip': self.to_display_text(raw_event),
                'formatted_value': self._format_metric_value(metric_name, metric_value),
                'unit': self.METRIC_UNITS.get(metric_name, '')
            }
            
        except Exception as e:
            return {
                'x': raw_event.get('step', -1),
                'y': 0,
                'error': str(e),
                'series': 'error'
            }
    
    def get_performance_summary(self, raw_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate performance summary from multiple events.
        
        Args:
            raw_events: List of raw performance monitor dictionaries
            
        Returns:
            Summary statistics and trends
        """
        if not raw_events:
            return {'error': 'No events provided'}
        
        try:
            # Group events by metric
            metrics_data = {}
            for event in raw_events:
                metric_name = event.get('metric_name', 'unknown')
                if metric_name not in metrics_data:
                    metrics_data[metric_name] = []
                metrics_data[metric_name].append(event.get('metric_value', 0.0))
            
            # Calculate statistics for each metric
            summary = {}
            for metric_name, values in metrics_data.items():
                if values:
                    summary[metric_name] = {
                        'count': len(values),
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values),
                        'latest': values[-1],
                        'unit': self.METRIC_UNITS.get(metric_name, ''),
                        'display_name': self.METRIC_DISPLAY_NAMES.get(metric_name, metric_name.title())
                    }
            
            return summary
            
        except Exception as e:
            return {'error': f'Summary generation error: {str(e)}'}
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _format_metric_value(self, metric_name: str, value: float) -> str:
        """Format metric value based on its type and expected precision."""
        try:
            # Time-based metrics (milliseconds)
            if metric_name in ['step_time', 'render_time', 'update_time']:
                return f"{value:.2f}"
            
            # Memory metrics (MB)
            elif metric_name == 'memory_usage':
                return f"{value:.1f}"
            
            # Rate metrics (per second)
            elif metric_name in ['trade_rate', 'collection_rate', 'mode_change_rate', 'fps']:
                return f"{value:.1f}"
            
            # Percentage metrics
            elif metric_name in ['resource_density', 'cpu_usage']:
                return f"{value:.1f}"
            
            # Count metrics (integers)
            elif metric_name in ['event_count', 'agent_count']:
                return str(int(value))
            
            # Default: 2 decimal places
            else:
                return f"{value:.2f}"
                
        except (ValueError, TypeError):
            return str(value)
    
    def _classify_performance_level(self, metric_name: str, value: float, threshold_exceeded: bool) -> str:
        """Classify performance level based on metric type and value."""
        if threshold_exceeded:
            return 'critical'
        
        # Simple heuristics based on common performance expectations
        if metric_name == 'fps':
            if value >= 60: return 'excellent'
            elif value >= 30: return 'good'
            elif value >= 15: return 'warning'
            else: return 'critical'
        
        elif metric_name == 'step_time':
            if value <= 16: return 'excellent'  # 60fps
            elif value <= 33: return 'good'     # 30fps
            elif value <= 66: return 'warning'  # 15fps
            else: return 'critical'
        
        elif metric_name == 'memory_usage':
            if value <= 100: return 'excellent'
            elif value <= 500: return 'good'
            elif value <= 1000: return 'warning'
            else: return 'critical'
        
        else:
            return 'good'  # Default assumption for unknown metrics
    
    def _get_metric_category(self, metric_name: str) -> str:
        """Get category for metric for organizational purposes."""
        performance_metrics = ['step_time', 'render_time', 'update_time', 'fps']
        memory_metrics = ['memory_usage']
        throughput_metrics = ['trade_rate', 'collection_rate', 'mode_change_rate', 'event_count']
        system_metrics = ['cpu_usage', 'agent_count', 'resource_density']
        
        if metric_name in performance_metrics:
            return 'performance'
        elif metric_name in memory_metrics:
            return 'memory'
        elif metric_name in throughput_metrics:
            return 'throughput'
        elif metric_name in system_metrics:
            return 'system'
        else:
            return 'other'
    
    def _normalize_metric_value(self, metric_name: str, value: float) -> float:
        """Normalize metric value to 0-1 scale for consistent charting."""
        # Simple normalization - in real implementation, these would be based on
        # expected ranges or historical data
        try:
            if metric_name == 'fps':
                return min(value / 60.0, 1.0)  # Normalize to 60fps max
            elif metric_name == 'step_time':
                return max(0.0, 1.0 - (value / 100.0))  # Lower time = better (inverted)
            elif metric_name == 'memory_usage':
                return min(value / 1000.0, 1.0)  # Normalize to 1GB max
            elif metric_name in ['cpu_usage', 'resource_density']:
                return value / 100.0  # Already percentages
            else:
                return min(value / 100.0, 1.0)  # Default normalization
        except (ValueError, TypeError, ZeroDivisionError):
            return 0.0
    
    def _get_threshold_severity(self, metric_name: str, value: float) -> str:
        """Determine severity level for threshold exceeded cases."""
        # Simple heuristics - in practice these would be configurable
        if metric_name == 'step_time' and value > 100:
            return 'critical'
        elif metric_name == 'memory_usage' and value > 2000:
            return 'critical'
        elif metric_name == 'fps' and value < 10:
            return 'critical'
        else:
            return 'warning'
    
    def _get_metric_color(self, metric_name: str, threshold_exceeded: bool) -> str:
        """Get color for metric visualization."""
        if threshold_exceeded:
            return '#FF0000'  # Red for threshold exceeded
        
        # Category-based colors
        category = self._get_metric_category(metric_name)
        colors = {
            'performance': '#2196F3',  # Blue
            'memory': '#FF9800',       # Orange  
            'throughput': '#4CAF50',   # Green
            'system': '#9C27B0',       # Purple
            'other': '#607D8B'         # Blue Grey
        }
        return colors.get(category, '#607D8B')