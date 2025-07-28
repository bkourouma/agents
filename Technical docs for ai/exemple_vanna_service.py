# vanna_service.py - Enhanced version with database-specific SQL generation and secure visualization support

import os
import logging
import json
import re
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
from db import (
    get_database_connection, get_table_schemas, get_table_schema_columns,
    get_database_connections
)

logger = logging.getLogger(__name__)

def setup_vanna_cache():
    """Setup Vanna cache directories with proper permissions"""
    cache_base = os.path.join(os.getcwd(), 'vanna_cache')
    
    # Create directories
    dirs = [
        cache_base,
        os.path.join(cache_base, 'models'),
        os.path.join(cache_base, 'chroma'),
        os.path.join(cache_base, 'sentence_transformers')
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    # Set environment variables for model caching BEFORE any imports
    os.environ['SENTENCE_TRANSFORMERS_HOME'] = os.path.join(cache_base, 'sentence_transformers')
    os.environ['TRANSFORMERS_CACHE'] = os.path.join(cache_base, 'models')
    os.environ['HF_HOME'] = os.path.join(cache_base, 'models')
    os.environ['CHROMA_CACHE_DIR'] = os.path.join(cache_base, 'chroma')
    
    logger.info(f"[OK] Vanna cache setup complete at: {cache_base}")
    return cache_base

# Call setup BEFORE any Vanna imports
VANNA_CACHE_DIR = setup_vanna_cache()

class VannaService:
    """Service to handle Vanna AI integration for natural language to SQL conversion with visualization."""
    
    def __init__(self):
        self.vanna_instances = {}  # Cache Vanna instances per connection
        self.connection_providers = {}  # Cache provider info per connection
        self._initialize_vanna_components()
        
        # Chart type detection patterns
        self.chart_patterns = {
            'time_series': ['over time', 'by date', 'trend', 'timeline', 'historical', 'par année', 'par mois'],
            'comparison': ['compare', 'comparer', 'versus', 'vs', 'difference between', 'entre', 'et', 'du cameroun et'],
            'distribution': ['distribution', 'spread', 'range', 'histogram'],
            'proportion': ['percentage', 'proportion', 'share', 'breakdown', 'pourcentage'],
            'ranking': ['top', 'bottom', 'highest', 'lowest', 'best', 'worst', 'meilleur', 'pire'],
            'relationship': ['correlation', 'relationship', 'scatter', 'vs']
        }
    
    def _initialize_vanna_components(self):
        """Initialize Vanna with OpenAI and ChromaDB components."""
        try:
            # Import after setting environment variables
            from vanna.openai.openai_chat import OpenAI_Chat
            from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
            
            class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
                def __init__(self, config=None):
                    # Ensure config uses our cache directory
                    if config and 'path' not in config:
                        config['path'] = os.path.join(VANNA_CACHE_DIR, 'chroma_default')
                    ChromaDB_VectorStore.__init__(self, config=config)
                    OpenAI_Chat.__init__(self, config=config)
                
                # Override generate_plotly_code for security
                def generate_plotly_code(self, question: str = None, sql: str = None, 
                                       df_metadata: str = None, **kwargs) -> str:
                    """Override to prevent code injection - returns empty string"""
                    logger.warning("Direct plotly code generation is disabled for security")
                    return ""
            
            self.VannaClass = MyVanna
            logger.info("[OK] Vanna components initialized successfully with security overrides")
            
        except ImportError as e:
            logger.error(f"[ERROR] Failed to import Vanna components: {e}")
            logger.error("Please install Vanna with: pip install 'vanna[chromadb,openai]'")
            raise ImportError(f"Vanna dependencies not found: {e}")
    
    def detect_chart_type(self, question: str, df: pd.DataFrame, sql_query: str) -> str:
        """Intelligently detect the best chart type based on question, data structure, and SQL."""
        question_lower = question.lower()
        
        # Check question patterns
        for chart_type, patterns in self.chart_patterns.items():
            if any(pattern in question_lower for pattern in patterns):
                logger.info(f"[CHART] Detected chart type from question pattern: {chart_type}")
                
                # Validate based on data structure
                if chart_type == 'time_series' and self._has_datetime_column(df):
                    return 'line'
                elif chart_type == 'comparison' and len(df.columns) >= 2:
                    # Check if it's a time-based comparison (should be line chart)
                    if self._has_time_column(df) or any('ann' in col.lower() for col in df.columns):
                        return 'line'
                    return 'bar'
                elif chart_type == 'distribution' and self._has_numeric_column(df):
                    return 'histogram'
                elif chart_type == 'proportion' and len(df) <= 10:
                    return 'pie'
                elif chart_type == 'ranking':
                    return 'bar'
                elif chart_type == 'relationship' and self._has_two_numeric_columns(df):
                    return 'scatter'
        
        # Fallback detection based on data structure
        return self._detect_chart_from_data(df, sql_query)
    
    def _detect_chart_from_data(self, df: pd.DataFrame, sql_query: str) -> str:
        """Detect chart type based on data structure and SQL query."""
        sql_upper = sql_query.upper()
        
        # Check for aggregation functions
        has_aggregation = any(func in sql_upper for func in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN'])
        
        # Analyze DataFrame structure
        num_rows = len(df)
        num_cols = len(df.columns)
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        # Decision tree for chart type
        if datetime_cols and numeric_cols:
            return 'line'  # Time series data
        elif has_aggregation and num_rows <= 20:
            return 'bar'  # Aggregated data
        elif num_rows <= 10 and num_cols == 2 and len(numeric_cols) == 1:
            return 'pie'  # Small categorical data
        elif len(numeric_cols) >= 2:
            return 'scatter'  # Multiple numeric columns
        elif num_rows > 50 and len(numeric_cols) == 1:
            return 'histogram'  # Distribution of single numeric column
        else:
            return 'bar'  # Default fallback
    
    def _has_datetime_column(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame has datetime columns."""
        return len(df.select_dtypes(include=['datetime64']).columns) > 0

    def _has_time_column(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame has time-related columns (datetime or year/month columns)."""
        # Check for datetime columns
        if self._has_datetime_column(df):
            return True

        # Check for year/month/date columns by name
        time_indicators = ['annee', 'year', 'mois', 'month', 'date', 'time', 'periode']
        for col in df.columns:
            col_lower = col.lower()
            if any(indicator in col_lower for indicator in time_indicators):
                return True

        return False
    
    def _has_numeric_column(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame has numeric columns."""
        return len(df.select_dtypes(include=['number']).columns) > 0
    
    def _has_two_numeric_columns(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame has at least two numeric columns."""
        return len(df.select_dtypes(include=['number']).columns) >= 2
    
    def generate_secure_plotly_config(self, df: pd.DataFrame, chart_type: str, 
                                    question: str, sql_query: str) -> Dict[str, Any]:
        """Generate secure Plotly configuration based on data and chart type."""
        try:
            logger.info(f"[CHART] Generating {chart_type} chart configuration")
            
            # Limit data size for performance
            if len(df) > 1000:
                logger.warning(f"Large dataset ({len(df)} rows), sampling to 1000 rows")
                df = df.sample(n=1000)
            
            # Generate chart based on type
            if chart_type == 'line':
                return self._generate_line_chart(df, question)
            elif chart_type == 'bar':
                return self._generate_bar_chart(df, question)
            elif chart_type == 'pie':
                return self._generate_pie_chart(df, question)
            elif chart_type == 'scatter':
                return self._generate_scatter_chart(df, question)
            elif chart_type == 'histogram':
                return self._generate_histogram_chart(df, question)
            else:
                return self._generate_bar_chart(df, question)  # Default
                
        except Exception as e:
            logger.error(f"[ERROR] Failed to generate chart configuration: {e}")
            return self._generate_error_chart(str(e))
    
    def _generate_line_chart(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """Generate line chart configuration with support for multi-series comparisons."""
        # Check if this is a comparison with multiple series
        is_comparison = self._is_comparison_data(df, question)

        if is_comparison and len(df.columns) >= 3:
            return self._generate_comparison_line_chart(df, question)

        # Standard single-series line chart
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

        if not datetime_cols or not numeric_cols:
            # Look for time-related columns by name
            time_col = None
            for col in df.columns:
                col_lower = col.lower()
                if any(indicator in col_lower for indicator in ['annee', 'year', 'mois', 'month', 'date']):
                    time_col = col
                    break

            x_col = time_col if time_col else df.columns[0]
            y_col = numeric_cols[0] if numeric_cols else df.columns[1] if len(df.columns) > 1 else None
        else:
            x_col = datetime_cols[0]
            y_col = numeric_cols[0]

        if x_col and y_col:
            fig = px.line(df, x=x_col, y=y_col,
                         title=f"Analysis: {question[:50]}...")

            # Customize layout
            fig.update_layout(
                xaxis_title=x_col,
                yaxis_title=y_col,
                hovermode='x unified',
                template='plotly_white'
            )

            return json.loads(fig.to_json())

        return self._generate_error_chart("Insufficient columns for line chart")

    def _generate_comparison_line_chart(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """Generate line chart with multiple series for time-based comparisons."""
        try:
            cols = df.columns.tolist()

            # Find the entity column (countries, products, etc.)
            entity_col = None
            for col in cols:
                col_lower = col.lower()
                if any(entity in col_lower for entity in ['pays', 'country', 'region', 'grossiste', 'produit']):
                    entity_col = col
                    break

            # Find time column
            time_col = None
            for col in cols:
                col_lower = col.lower()
                if any(indicator in col_lower for indicator in ['annee', 'year', 'mois', 'month', 'date', 'time']):
                    time_col = col
                    break

            # Find numeric column (value)
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            value_col = numeric_cols[0] if numeric_cols else cols[-1]

            if not all([entity_col, time_col, value_col]):
                # Fallback to standard line chart
                return self._generate_standard_line_chart(df, question)

            # Create multi-series line chart
            fig = px.line(
                df,
                x=time_col,
                y=value_col,
                color=entity_col,
                title=f"Comparison: {question[:50]}...",
                markers=True
            )

            # Customize layout for better comparison visualization
            fig.update_layout(
                xaxis_title=time_col,
                yaxis_title=value_col,
                template='plotly_white',
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )

            # Format numbers on hover
            fig.update_traces(
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             f'{time_col}: %{{x}}<br>' +
                             f'{value_col}: %{{y:,.0f}}<extra></extra>'
            )

            logger.info(f"[CHART] Generated comparison line chart with {df[entity_col].nunique()} series")
            return json.loads(fig.to_json())

        except Exception as e:
            logger.error(f"[ERROR] Failed to generate comparison line chart: {e}")
            return self._generate_standard_line_chart(df, question)

    def _generate_standard_line_chart(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """Generate standard single-series line chart."""
        x_col = df.columns[0]
        y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

        fig = px.line(df, x=x_col, y=y_col, title=f"Analysis: {question[:50]}...")

        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col,
            hovermode='x unified',
            template='plotly_white'
        )

        return json.loads(fig.to_json())
    
    def _generate_bar_chart(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """Generate bar chart configuration with support for country/series comparisons."""
        if len(df.columns) >= 2:
            # Detect if this is a country/series comparison
            is_comparison = self._is_comparison_data(df, question)

            if is_comparison and len(df.columns) >= 3:
                # Handle multi-series comparison (e.g., countries over time)
                return self._generate_comparison_bar_chart(df, question)
            else:
                # Standard single-series bar chart
                x_col = df.columns[0]
                y_col = df.columns[1]

                # Limit categories if too many
                if len(df) > 30:
                    df = df.nlargest(30, y_col) if pd.api.types.is_numeric_dtype(df[y_col]) else df.head(30)

                fig = px.bar(df, x=x_col, y=y_col,
                            title=f"Analysis: {question[:50]}...")

                # Customize layout
                fig.update_layout(
                    xaxis_title=x_col,
                    yaxis_title=y_col,
                    template='plotly_white',
                    xaxis_tickangle=-45 if len(df) > 10 else 0
                )

                return json.loads(fig.to_json())

        return self._generate_error_chart("Insufficient columns for bar chart")

    def _is_comparison_data(self, df: pd.DataFrame, question: str) -> bool:
        """Detect if the data represents a comparison between entities."""
        question_lower = question.lower()

        # Check for comparison keywords
        comparison_keywords = ['comparer', 'compare', 'versus', 'vs', 'entre', 'between']
        has_comparison_keyword = any(keyword in question_lower for keyword in comparison_keywords)

        if not has_comparison_keyword:
            return False

        # Method 1: Check for entity columns (long format)
        potential_entity_cols = []
        for col in df.columns:
            col_lower = col.lower()
            if any(entity in col_lower for entity in ['pays', 'country', 'region', 'grossiste', 'produit']):
                potential_entity_cols.append(col)

        # Check if we have multiple entities in the data (long format)
        has_multiple_entities = False
        if potential_entity_cols:
            for col in potential_entity_cols:
                if df[col].nunique() > 1:
                    has_multiple_entities = True
                    break

        if has_multiple_entities and len(df.columns) >= 3:
            return True

        # Method 2: Check for country-specific columns (wide format)
        # Look for columns that contain country names
        country_columns = []
        country_indicators = ['cameroun', 'cameroon', 'cote', 'ivoire', 'ivory', 'senegal', 'mali', 'burkina']

        for col in df.columns:
            col_lower = col.lower()
            if any(country in col_lower for country in country_indicators):
                country_columns.append(col)

        # If we have multiple country-specific columns, it's a comparison
        if len(country_columns) >= 2:
            return True

        return False

    def _generate_comparison_bar_chart(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """Generate bar chart with multiple series for comparisons."""
        try:
            cols = df.columns.tolist()

            # Method 1: Check for wide format (country-specific columns)
            country_columns = []
            country_indicators = ['cameroun', 'cameroon', 'cote', 'ivoire', 'ivory', 'senegal', 'mali', 'burkina']

            for col in cols:
                col_lower = col.lower()
                if any(country in col_lower for country in country_indicators):
                    country_columns.append(col)

            if len(country_columns) >= 2:
                # Wide format: transform to long format for plotting
                return self._generate_wide_format_comparison_chart(df, country_columns, question)

            # Method 2: Long format (original logic)
            # Find the entity column (countries, products, etc.)
            entity_col = None
            for col in cols:
                col_lower = col.lower()
                if any(entity in col_lower for entity in ['pays', 'country', 'region', 'grossiste', 'produit']):
                    entity_col = col
                    break

            # Find numeric column (value)
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            value_col = numeric_cols[0] if numeric_cols else cols[-1]

            # Find the category/time column (remaining column)
            category_col = None
            for col in cols:
                if col != entity_col and col != value_col:
                    category_col = col
                    break

            if not all([entity_col, category_col, value_col]):
                # Fallback to standard bar chart
                return self._generate_standard_bar_chart(df, question)

            # Create grouped bar chart
            fig = px.bar(
                df,
                x=category_col,
                y=value_col,
                color=entity_col,
                title=f"Comparison: {question[:50]}...",
                barmode='group'  # This creates side-by-side bars
            )

            # Customize layout for better comparison visualization
            fig.update_layout(
                xaxis_title=category_col,
                yaxis_title=value_col,
                template='plotly_white',
                xaxis_tickangle=-45 if len(df[category_col].unique()) > 5 else 0,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hovermode='x unified'
            )

            # Format numbers on hover
            fig.update_traces(
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             f'{category_col}: %{{x}}<br>' +
                             f'{value_col}: %{{y:,.0f}}<extra></extra>'
            )

            logger.info(f"[CHART] Generated comparison bar chart with {df[entity_col].nunique()} series")
            return json.loads(fig.to_json())

        except Exception as e:
            logger.error(f"[ERROR] Failed to generate comparison bar chart: {e}")
            return self._generate_standard_bar_chart(df, question)

    def _generate_wide_format_comparison_chart(self, df: pd.DataFrame, country_columns: List[str], question: str) -> Dict[str, Any]:
        """Generate comparison chart from wide format data (separate columns for each country)."""
        try:
            # Find the category column (usually the first non-country column)
            category_col = None
            for col in df.columns:
                if col not in country_columns:
                    category_col = col
                    break

            if not category_col:
                return self._generate_error_chart("No category column found for comparison")

            # Transform wide format to long format
            melted_data = []
            for _, row in df.iterrows():
                category_value = row[category_col]
                for country_col in country_columns:
                    # Extract country name from column name
                    country_name = self._extract_country_name(country_col)
                    value = row[country_col]
                    melted_data.append({
                        'Category': category_value,
                        'Country': country_name,
                        'Value': value
                    })

            # Create DataFrame from melted data
            melted_df = pd.DataFrame(melted_data)

            # Create grouped bar chart
            fig = px.bar(
                melted_df,
                x='Category',
                y='Value',
                color='Country',
                title=f"Comparison: {question[:50]}...",
                barmode='group'  # This creates side-by-side bars
            )

            # Customize layout for better comparison visualization
            fig.update_layout(
                xaxis_title=category_col,
                yaxis_title='Value',
                template='plotly_white',
                xaxis_tickangle=-45 if len(melted_df['Category'].unique()) > 5 else 0,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                margin=dict(t=80, b=80, l=60, r=60),
                height=500
            )

            # Format y-axis for large numbers
            if melted_df['Value'].max() > 1000000:
                fig.update_layout(yaxis_tickformat='.2s')

            return json.loads(fig.to_json())

        except Exception as e:
            logger.error(f"[ERROR] Failed to generate wide format comparison chart: {e}")
            return self._generate_error_chart(str(e))

    def _extract_country_name(self, column_name: str) -> str:
        """Extract readable country name from column name."""
        col_lower = column_name.lower()

        # Map common patterns to readable names
        if 'cameroun' in col_lower or 'cameroon' in col_lower:
            return 'Cameroun'
        elif 'cote' in col_lower and 'ivoire' in col_lower:
            return 'Côte d\'Ivoire'
        elif 'senegal' in col_lower:
            return 'Sénégal'
        elif 'mali' in col_lower:
            return 'Mali'
        elif 'burkina' in col_lower:
            return 'Burkina Faso'
        else:
            # Fallback: clean up the column name
            return column_name.replace('CA_', '').replace('_', ' ').title()

    def _generate_standard_bar_chart(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """Generate standard single-series bar chart."""
        x_col = df.columns[0]
        y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

        fig = px.bar(df, x=x_col, y=y_col, title=f"Analysis: {question[:50]}...")

        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col,
            template='plotly_white',
            xaxis_tickangle=-45 if len(df) > 10 else 0
        )

        return json.loads(fig.to_json())
    
    def _generate_pie_chart(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """Generate pie chart configuration."""
        if len(df.columns) >= 2 and len(df) <= 20:  # Pie charts work best with limited categories
            names_col = df.columns[0]
            values_col = df.columns[1]
            
            fig = px.pie(df, names=names_col, values=values_col,
                        title=f"Analysis: {question[:50]}...")
            
            # Customize layout
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(template='plotly_white')
            
            return json.loads(fig.to_json())
        
        return self._generate_error_chart("Data not suitable for pie chart")
    
    def _generate_scatter_chart(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """Generate scatter plot configuration."""
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            
            fig = px.scatter(df, x=x_col, y=y_col,
                           title=f"Analysis: {question[:50]}...")
            
            # Add trendline if appropriate
            if len(df) > 10:
                fig = px.scatter(df, x=x_col, y=y_col, trendline="ols",
                               title=f"Analysis: {question[:50]}...")
            
            # Customize layout
            fig.update_layout(
                xaxis_title=x_col,
                yaxis_title=y_col,
                template='plotly_white'
            )
            
            return json.loads(fig.to_json())
        
        return self._generate_error_chart("Insufficient numeric columns for scatter plot")
    
    def _generate_histogram_chart(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """Generate histogram configuration."""
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if numeric_cols:
            col = numeric_cols[0]
            
            fig = px.histogram(df, x=col, nbins=30,
                             title=f"Distribution: {question[:50]}...")
            
            # Customize layout
            fig.update_layout(
                xaxis_title=col,
                yaxis_title="Count",
                template='plotly_white',
                bargap=0.1
            )
            
            return json.loads(fig.to_json())
        
        return self._generate_error_chart("No numeric columns for histogram")
    
    def _generate_error_chart(self, error_message: str) -> Dict[str, Any]:
        """Generate an error placeholder chart."""
        fig = go.Figure()
        fig.add_annotation(
            text=f"Unable to generate chart: {error_message}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        fig.update_layout(
            title="Visualization Error",
            template='plotly_white',
            height=400
        )
        return json.loads(fig.to_json())
    
    async def ask_question_with_visualization(self, connection_id: int, question: str,
                                            execute_query: bool = True) -> Dict:
        """
        Ask a question and generate both SQL results and visualization.
        Returns complete response with SQL, results, and chart configuration.
        """
        logger.info(f"💬 Processing question with visualization: '{question}'")
        
        try:
            # First, get SQL and results using existing method
            result = await self.ask_question(connection_id, question, execute_query)
            
            if not result['success'] or not execute_query:
                return result
            
            # Convert results to DataFrame for visualization
            if result['results']:
                df = pd.DataFrame(result['results'])
                
                # Detect optimal chart type
                chart_type = self.detect_chart_type(question, df, result['sql_query'])
                logger.info(f"[CHART] Selected chart type: {chart_type}")
                
                # Generate secure chart configuration
                chart_config = self.generate_secure_plotly_config(
                    df, chart_type, question, result['sql_query']
                )
                
                # Add visualization to result
                result['visualization'] = {
                    'chart_type': chart_type,
                    'plotly_config': chart_config,
                    'supported_types': ['line', 'bar', 'pie', 'scatter', 'histogram']
                }
                
                logger.info(f"[OK] Successfully generated {chart_type} visualization")
            else:
                result['visualization'] = None
                logger.info("[CHART] No data to visualize")
            
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to generate visualization: {e}")
            # Return result without visualization on error
            if 'result' in locals():
                result['visualization'] = None
                result['visualization_error'] = str(e)
                return result
            else:
                return {
                    'sql_query': '',
                    'results': [],
                    'explanation': f"Error: {str(e)}",
                    'success': False,
                    'error': str(e),
                    'visualization': None
                }
    
    def get_vanna_instance(self, connection_id: int) -> 'MyVanna':
        """Get or create a Vanna instance for a specific database connection."""
        logger.info(f"[REFRESH] Getting Vanna instance for connection {connection_id}")
        
        if connection_id not in self.vanna_instances:
            # Get connection info
            connection_info = get_database_connection(connection_id)
            if not connection_info:
                raise ValueError(f"Connection {connection_id} not found")
            
            # Parse connection info
            conn_id, tenant_id, db_name, provider, conn_string = connection_info[:5]
            logger.info(f"[CHART] Connection details: {db_name} ({provider})")
            
            # Store provider info
            self.connection_providers[connection_id] = provider.lower()
            
            # Configure Vanna with custom cache directory
            config = {
                'api_key': os.getenv('OPENAI_API_KEY'),
                'model': os.getenv('VANNA_MODEL', 'gpt-3.5-turbo'),
                'path': os.path.join(VANNA_CACHE_DIR, f'chroma_db_{connection_id}'),
            }
            
            if not config['api_key']:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            
            logger.info(f"[AI] Creating Vanna instance with model: {config['model']}")
            logger.info(f"[FOLDER] Using ChromaDB path: {config['path']}")
            
            # Create Vanna instance
            vn = self.VannaClass(config=config)

            # Enable LLM to see data for better introspection BEFORE any training or connection
            # This allows Vanna to examine actual data when needed for complex queries
            vn.allow_llm_to_see_data = True
            logger.info("[SECURITY] Enabled allow_llm_to_see_data for database introspection")

            # Connect to the database AFTER enabling data access
            self._connect_vanna_to_database(vn, provider, conn_string)

            # Train the model with schema AND database-specific syntax
            self._train_vanna_with_schema(vn, connection_id, provider)
            
            self.vanna_instances[connection_id] = vn
            logger.info(f"[OK] Vanna instance created and trained for connection {connection_id}")
        
        return self.vanna_instances[connection_id]
    
    def _get_database_specific_syntax_docs(self, provider: str) -> str:
        """Get database-specific SQL syntax documentation."""
        provider_lower = provider.lower()
        
        if provider_lower == 'sqlserver':
            return """
            IMPORTANT SQL Server Syntax Rules:
            - Use TOP N instead of LIMIT N (e.g., SELECT TOP 10 * FROM table)
            - Use OFFSET...FETCH for pagination: OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY
            - String concatenation uses + operator
            - Use GETDATE() for current timestamp
            - Use square brackets [table_name] for identifiers with spaces or reserved words
            - BOOLEAN type doesn't exist, use BIT (0 or 1)
            - Auto-increment is IDENTITY(1,1)
            - For strings with apostrophes, use double apostrophes: 'Côte d''Ivoire' NOT 'Côte d\'Ivoire'
            - French text examples: 'Côte d''Ivoire', 'L''entreprise', 'C''est'
            """
        elif provider_lower == 'postgresql':
            return """
            PostgreSQL Syntax Rules:
            - Use LIMIT N for limiting results (e.g., SELECT * FROM table LIMIT 10)
            - Use OFFSET N for pagination
            - String concatenation uses || operator
            - Use NOW() or CURRENT_TIMESTAMP for current timestamp
            - Use double quotes "table_name" for case-sensitive identifiers
            - Supports BOOLEAN type
            - Auto-increment is SERIAL or IDENTITY
            """
        elif provider_lower == 'mysql':
            return """
            MySQL Syntax Rules:
            - Use LIMIT N for limiting results (e.g., SELECT * FROM table LIMIT 10)
            - Use LIMIT offset, count for pagination
            - String concatenation uses CONCAT() function
            - Use NOW() for current timestamp
            - Use backticks `table_name` for identifiers
            - BOOLEAN is alias for TINYINT(1)
            - Auto-increment is AUTO_INCREMENT
            """
        else:
            return """
            SQLite Syntax Rules:
            - Use LIMIT N for limiting results
            - Use LIMIT count OFFSET offset for pagination
            - String concatenation uses || operator
            - Use datetime('now') for current timestamp
            - Use double quotes or square brackets for identifiers
            - No native BOOLEAN type, use INTEGER (0 or 1)
            - Auto-increment is AUTOINCREMENT
            """
    
    def _train_vanna_with_schema(self, vn, connection_id: int, provider: str):
        """Train Vanna with the database schema and metadata."""
        logger.info(f"[TRAIN] Training Vanna for connection {connection_id} ({provider})")
        
        try:
            # First, add database-specific syntax documentation
            syntax_docs = self._get_database_specific_syntax_docs(provider)
            vn.train(documentation=syntax_docs)
            logger.info(f"[OK] Added {provider} syntax documentation")
            
            # Add specific examples for common queries in the correct syntax
            if provider.lower() == 'sqlserver':
                example_queries = [
                    ("Show me the first 10 records", "SELECT TOP 10 * FROM table_name"),
                    ("Get the last 5 entries", "SELECT TOP 5 * FROM table_name ORDER BY id DESC"),
                    ("Show records 11-20", "SELECT * FROM table_name ORDER BY id OFFSET 10 ROWS FETCH NEXT 10 ROWS ONLY"),
                    ("Show data for Côte d'Ivoire", "SELECT * FROM v_VentesParPays WHERE Pays = 'Côte d''Ivoire'"),
                    ("Find records for L'entreprise", "SELECT * FROM table_name WHERE nom = 'L''entreprise'"),
                    ("Data from Cameroun and Côte d'Ivoire", "SELECT * FROM v_VentesParPays WHERE Pays IN ('Cameroun', 'Côte d''Ivoire')"),
                    ("Compare sales between countries", "SELECT Pays, Annee, Mois, ChiffreAffairesTotal FROM v_VentesParPays WHERE Pays IN ('Cameroun', 'Côte d''Ivoire') ORDER BY Annee, Mois, Pays"),
                ]
            else:
                example_queries = [
                    ("Show me the first 10 records", "SELECT * FROM table_name LIMIT 10"),
                    ("Get the last 5 entries", "SELECT * FROM table_name ORDER BY id DESC LIMIT 5"),
                    ("Show records 11-20", "SELECT * FROM table_name LIMIT 10 OFFSET 10"),
                ]
            
            for question, sql in example_queries:
                vn.train(question=question, sql=sql)

            # Add specific training for French country comparisons
            if provider.lower() == 'sqlserver':
                french_examples = [
                    ("Comparer les chiffres d'affaires du Cameroun et de la Côte d'Ivoire de 2019 à 2020",
                     "SELECT Annee, Mois, Pays, ChiffreAffairesTotal FROM v_VentesParPays WHERE Pays IN ('Cameroun', 'Côte d''Ivoire') AND Annee BETWEEN 2019 AND 2020 ORDER BY Annee, Mois, Pays"),
                    ("Ventes par pays pour la Côte d'Ivoire",
                     "SELECT * FROM v_VentesParPays WHERE Pays = 'Côte d''Ivoire'"),
                    ("Données du Cameroun en 2020",
                     "SELECT * FROM v_VentesParPays WHERE Pays = 'Cameroun' AND Annee = 2020"),
                ]

                for question, sql in french_examples:
                    vn.train(question=question, sql=sql)
                    logger.debug(f"🇫🇷 Added French training example: {question}")

            logger.info(f"[OK] Added {len(example_queries)} syntax examples for {provider}")
            
            # Get table schemas for this connection
            table_schemas = get_table_schemas(connection_id)
            
            if not table_schemas:
                logger.warning(f"[WARNING] No table schemas found for connection {connection_id}")
                return
            
            training_data_count = 0
            
            for schema in table_schemas:
                schema_id = schema[0]
                table_name = schema[2]  # display name
                real_table_name = schema[3]
                table_description = schema[4]
                
                logger.info(f"[LIST] Training table: {real_table_name} ({table_name})")
                
                # Get columns for this table
                columns = get_table_schema_columns(schema_id)
                
                # Build DDL statement
                ddl_parts = [f"CREATE TABLE {real_table_name} ("]
                column_descriptions = []
                
                for col in columns:
                    col_name = col[2]  # real_column_name
                    data_type = col[4]
                    is_nullable = bool(col[5])
                    sample_data = col[6]
                    col_description = col[7]
                    
                    # Add column to DDL
                    nullable_str = "" if is_nullable else " NOT NULL"
                    ddl_parts.append(f"    {col_name} {data_type}{nullable_str},")
                    
                    # Collect column descriptions
                    if col_description or sample_data:
                        desc_parts = []
                        if col_description:
                            desc_parts.append(col_description)
                        if sample_data:
                            desc_parts.append(f"Sample values: {sample_data}")
                        column_descriptions.append(f"{col_name}: {'; '.join(desc_parts)}")
                
                # Complete DDL
                if ddl_parts[-1].endswith(','):
                    ddl_parts[-1] = ddl_parts[-1][:-1]  # Remove last comma
                ddl_parts.append(");")
                
                ddl_statement = "\n".join(ddl_parts)
                
                # Train with DDL
                logger.debug(f"📝 Adding DDL: {ddl_statement}")
                vn.train(ddl=ddl_statement)
                training_data_count += 1
                
                # Train with table documentation
                if table_description:
                    doc = f"Table {real_table_name}: {table_description}"
                    logger.debug(f"[HELP] Adding documentation: {doc}")
                    vn.train(documentation=doc)
                    training_data_count += 1
                
                # Train with column documentation
                if column_descriptions:
                    column_doc = f"Table {real_table_name} columns: " + "; ".join(column_descriptions)
                    logger.debug(f"[CHART] Adding column documentation")
                    vn.train(documentation=column_doc)
                    training_data_count += 1
                
                # Add database-specific example queries
                if provider.lower() == 'sqlserver':
                    example_queries = [
                        f"SELECT TOP 10 * FROM {real_table_name}",
                        f"SELECT COUNT(*) FROM {real_table_name}",
                        f"SELECT TOP 1 * FROM {real_table_name} ORDER BY 1 DESC",
                    ]
                else:
                    example_queries = [
                        f"SELECT * FROM {real_table_name} LIMIT 10",
                        f"SELECT COUNT(*) FROM {real_table_name}",
                        f"SELECT * FROM {real_table_name} ORDER BY 1 DESC LIMIT 1",
                    ]
                
                for query in example_queries:
                    logger.debug(f"[SEARCH] Adding example query: {query}")
                    vn.train(sql=query)
                    training_data_count += 1
            
            logger.info(f"[OK] Vanna training completed for connection {connection_id}. "
                       f"Added {training_data_count} training items for {len(table_schemas)} tables.")
                       
        except Exception as e:
            logger.error(f"[ERROR] Failed to train Vanna with schema: {e}")
            raise
    
    def _connect_vanna_to_database(self, vn, provider: str, connection_string: str):
        """Connect Vanna to the database based on provider type."""
        logger.info(f"[CONNECT] Connecting Vanna to {provider} database")
        
        try:
            if provider.lower() == 'postgresql':
                # Parse PostgreSQL connection string
                if connection_string.startswith('postgresql://'):
                    vn.connect_to_postgres(dsn=connection_string)
                elif '=' in connection_string and ';' in connection_string:
                    # Parse semicolon-separated format
                    params = self._parse_connection_params(connection_string)
                    vn.connect_to_postgres(
                        host=params.get('host', 'localhost'),
                        dbname=params.get('dbname', ''),
                        user=params.get('user', ''),
                        password=params.get('password', ''),
                        port=int(params.get('port', 5432))
                    )
                else:
                    vn.connect_to_postgres(dsn=connection_string)
            
            elif provider.lower() == 'mysql':
                params = self._parse_connection_params(connection_string)
                # Use custom connection for MySQL
                self._setup_mysql_connection(vn, params)
            
            elif provider.lower() == 'sqlserver':
                # Use custom connection for SQL Server with enhanced driver handling
                self._setup_sqlserver_connection(vn, connection_string)
            
            elif provider.lower() == 'sqlite':
                # Use custom connection for SQLite
                self._setup_sqlite_connection(vn, connection_string)
            
            else:
                raise ValueError(f"Unsupported database provider: {provider}")
                
            logger.info(f"[OK] Successfully connected Vanna to {provider}")
                
        except Exception as e:
            logger.error(f"[ERROR] Failed to connect Vanna to database: {e}")
            raise
    
    def _parse_connection_params(self, connection_string: str) -> Dict[str, str]:
        """Parse connection string parameters."""
        params = {}
        for param in connection_string.split(';'):
            if '=' in param:
                key, value = param.split('=', 1)
                key = key.strip().lower()
                value = value.strip()
                
                # Map common parameter names
                if key in ['host', 'server']:
                    params['host'] = value
                elif key == 'port':
                    params['port'] = value
                elif key in ['database', 'db']:
                    params['dbname'] = value
                elif key in ['username', 'user', 'uid']:
                    params['user'] = value
                elif key in ['password', 'pwd']:
                    params['password'] = value
        
        return params
    
    def _setup_mysql_connection(self, vn, params: Dict[str, str]):
        """Setup MySQL connection for Vanna."""
        import pandas as pd
        import pymysql
        
        logger.info(f"[SETUP] Setting up MySQL connection with params: {list(params.keys())}")
        
        def run_sql(sql: str) -> pd.DataFrame:
            logger.debug(f"[SEARCH] Executing MySQL query: {sql}")
            conn = pymysql.connect(
                host=params.get('host', 'localhost'),
                user=params.get('user', 'root'),
                password=params.get('password', ''),
                database=params.get('dbname', ''),
                port=int(params.get('port', 3306))
            )
            result = pd.read_sql(sql, conn)
            conn.close()
            logger.debug(f"[OK] MySQL query returned {len(result)} rows")
            return result
        
        vn.run_sql = run_sql
        vn.run_sql_is_set = True
    
    def _setup_sqlserver_connection(self, vn, connection_string: str):
        """Setup SQL Server connection for Vanna with enhanced driver handling."""
        import pandas as pd
        import pyodbc
        from sqlalchemy import create_engine
        
        logger.info(f"[SETUP] Setting up SQL Server connection")
        logger.debug(f"Connection string preview: {connection_string[:50]}...")
        
        # List of drivers to try in order of preference
        drivers = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server", 
            "ODBC Driver 13 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server"
        ]
        
        # Check available drivers
        available_drivers = pyodbc.drivers()
        logger.info(f"[LIST] Available ODBC drivers: {list(available_drivers)}")
        
        # Find the best driver
        working_connection_string = None
        
        if "Driver=" not in connection_string and "DRIVER=" not in connection_string:
            for driver in drivers:
                if driver in available_drivers:
                    test_conn_string = f"Driver={{{driver}}};{connection_string}"
                    try:
                        # Test the connection
                        test_conn = pyodbc.connect(test_conn_string)
                        test_conn.close()
                        working_connection_string = test_conn_string
                        logger.info(f"[OK] Found working driver: {driver}")
                        break
                    except Exception as e:
                        logger.debug(f"[ERROR] Driver {driver} failed: {e}")
                        continue
            
            if not working_connection_string:
                # Try without explicit driver as last resort
                try:
                    test_conn = pyodbc.connect(connection_string)
                    test_conn.close()
                    working_connection_string = connection_string
                    logger.info("[OK] Connection works without explicit driver")
                except Exception as e:
                    logger.error(f"[ERROR] No working SQL Server driver found: {e}")
                    raise ValueError(f"No suitable SQL Server ODBC driver available. Available drivers: {list(available_drivers)}")
        else:
            # Driver already specified
            working_connection_string = connection_string
            logger.info("[OK] Using provided connection string with explicit driver")
        
        def run_sql(sql: str) -> pd.DataFrame:
            logger.debug(f"[SEARCH] Executing SQL Server query: {sql}")
            try:
                # Create SQLAlchemy engine for better pandas compatibility
                engine = create_engine(f"mssql+pyodbc:///?odbc_connect={working_connection_string}")
                result = pd.read_sql(sql, engine)
                engine.dispose()
                logger.debug(f"[OK] SQL Server query returned {len(result)} rows")
                return result
            except Exception as e:
                logger.error(f"[ERROR] SQL Server query failed: {e}")
                raise
        
        vn.run_sql = run_sql
        vn.run_sql_is_set = True
    
    def _setup_sqlite_connection(self, vn, connection_string: str):
        """Setup SQLite connection for Vanna."""
        import pandas as pd
        import sqlite3
        from sqlalchemy import create_engine
        
        # Extract database path
        if "Data Source=" in connection_string:
            db_path = connection_string.split("Data Source=")[1].split(";")[0]
        else:
            db_path = connection_string
        
        logger.info(f"[SETUP] Setting up SQLite connection to: {db_path}")
        
        def run_sql(sql: str) -> pd.DataFrame:
            logger.debug(f"[SEARCH] Executing SQLite query: {sql}")
            # Use SQLAlchemy for better pandas compatibility
            engine = create_engine(f"sqlite:///{db_path}")
            result = pd.read_sql(sql, engine)
            engine.dispose()
            logger.debug(f"[OK] SQLite query returned {len(result)} rows")
            return result
        
        vn.run_sql = run_sql
        vn.run_sql_is_set = True
    
    async def generate_sql_from_question(self, connection_id: int, question: str) -> Tuple[str, str]:
        """
        Generate SQL from natural language question.
        Returns: (sql_query, explanation)
        """
        logger.info(f"[AI] Generating SQL for question: '{question}'")
        
        try:
            vn = self.get_vanna_instance(connection_id)
            
            # Get the provider for this connection
            provider = self.connection_providers.get(connection_id, 'unknown')
            
            # Add database-specific context to the question
            if provider == 'sqlserver':
                context_hint = " (Remember: Use TOP instead of LIMIT for SQL Server)"
            else:
                context_hint = ""
            
            # Generate SQL
            sql_query = vn.generate_sql(question + context_hint)
            logger.debug(f"[SEARCH] Generated SQL: {sql_query}")
            
            if not sql_query:
                raise ValueError("Could not generate SQL for the given question")
            
            # Validate and fix SQL if needed
            sql_query = self._fix_sql_syntax(sql_query, provider)
            
            # Validate the SQL
            if not vn.is_sql_valid(sql_query):
                logger.warning(f"[WARNING] Generated SQL failed validation: {sql_query}")
                raise ValueError("Generated SQL is invalid")
            
            # Create explanation
            explanation = f"Generated SQL query to answer: '{question}'"
            
            logger.info(f"[OK] SQL generation successful")
            return sql_query, explanation
            
        except Exception as e:
            logger.error(f"[ERROR] SQL generation failed: {e}")
            raise ValueError(f"Failed to generate SQL: {str(e)}")
    
    def _fix_sql_syntax(self, sql_query: str, provider: str) -> str:
        """Fix common SQL syntax issues based on the database provider."""
        if not sql_query:
            return sql_query

        provider_lower = provider.lower()

        if provider_lower == 'sqlserver':
            # Fix LIMIT clause for SQL Server
            import re

            # Fix French text with apostrophes for SQL Server
            # Replace \' with '' (SQL Server standard)
            sql_query = re.sub(r"\\(')", r"''", sql_query)
            logger.debug(f"[SETUP] Fixed SQL: Converted escaped apostrophes for SQL Server")

            # Replace LIMIT N with TOP N
            limit_match = re.search(r'\sLIMIT\s+(\d+)\s*$', sql_query, re.IGNORECASE)
            if limit_match:
                limit_num = limit_match.group(1)
                # Remove LIMIT clause
                sql_query = sql_query[:limit_match.start()]
                # Add TOP after SELECT
                sql_query = re.sub(r'SELECT\s+', f'SELECT TOP {limit_num} ', sql_query, count=1, flags=re.IGNORECASE)
                logger.info(f"[SETUP] Fixed SQL: Converted LIMIT to TOP for SQL Server")

            # Fix LIMIT with OFFSET for SQL Server
            limit_offset_match = re.search(r'\sLIMIT\s+(\d+)\s+OFFSET\s+(\d+)\s*$', sql_query, re.IGNORECASE)
            if limit_offset_match:
                limit_num = limit_offset_match.group(1)
                offset_num = limit_offset_match.group(2)
                # Remove LIMIT OFFSET clause
                sql_query = sql_query[:limit_offset_match.start()]
                # Add OFFSET...FETCH
                sql_query += f' OFFSET {offset_num} ROWS FETCH NEXT {limit_num} ROWS ONLY'
                logger.info(f"[SETUP] Fixed SQL: Converted LIMIT OFFSET to OFFSET...FETCH for SQL Server")

        return sql_query
    
    async def ask_question(self, connection_id: int, question: str, 
                          execute_query: bool = True) -> Dict:
        """
        Ask a question and optionally execute the generated SQL.
        Returns complete response with SQL, results, and explanation.
        """
        logger.info(f"💬 Processing question: '{question}' (execute: {execute_query})")
        
        try:
            vn = self.get_vanna_instance(connection_id)
            
            if execute_query:
                # Generate SQL first with database-specific handling
                sql_query, explanation = await self.generate_sql_from_question(connection_id, question)
                logger.info(f"[SEARCH] Generated SQL: {sql_query}")
                
                # Execute the SQL
                try:
                    df_result = vn.run_sql(sql_query)
                    
                    # Proper DataFrame handling
                    if df_result is not None and isinstance(df_result, pd.DataFrame) and not df_result.empty:
                        results = df_result.to_dict('records')
                        logger.info(f"[OK] Query executed successfully, returned {len(results)} rows")
                    else:
                        results = []
                        logger.info("[OK] Query executed successfully, no rows returned")
                    
                    return {
                        'sql_query': sql_query,
                        'results': results,
                        'explanation': explanation,
                        'success': True
                    }
                    
                except Exception as e:
                    logger.error(f"[ERROR] Query execution failed: {e}")
                    return {
                        'sql_query': sql_query,
                        'results': [],
                        'explanation': f"Query generated but execution failed: {str(e)}",
                        'success': False,
                        'error': str(e)
                    }
            else:
                # Just generate SQL without execution
                sql_query, explanation = await self.generate_sql_from_question(connection_id, question)
                return {
                    'sql_query': sql_query,
                    'results': [],
                    'explanation': explanation,
                    'success': True
                }
                
        except Exception as e:
            logger.error(f"[ERROR] Vanna ask failed: {e}")
            return {
                'sql_query': '',
                'results': [],
                'explanation': f"Error: {str(e)}",
                'success': False,
                'error': str(e)
            }
    
    def retrain_connection(self, connection_id: int):
        """Retrain Vanna for a specific connection (useful after schema changes)."""
        logger.info(f"[REFRESH] Retraining Vanna for connection {connection_id}")
        
        try:
            # Remove existing instance to force retraining
            if connection_id in self.vanna_instances:
                del self.vanna_instances[connection_id]
                logger.info("🗑️ Removed existing Vanna instance")
            
            # Remove cached provider info
            if connection_id in self.connection_providers:
                del self.connection_providers[connection_id]
            
            # Create new instance (will automatically train)
            self.get_vanna_instance(connection_id)
            logger.info(f"[OK] Vanna retrained for connection {connection_id}")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to retrain Vanna: {e}")
            raise
    
    def get_training_data(self, connection_id: int) -> List[Dict]:
        """Get training data for a specific connection."""
        logger.debug(f"[CHART] Getting training data for connection {connection_id}")
        
        try:
            vn = self.get_vanna_instance(connection_id)
            training_data = vn.get_training_data()
            
            # Proper handling of training data result
            if isinstance(training_data, pd.DataFrame):
                if not training_data.empty:
                    training_data = training_data.to_dict('records')
                else:
                    training_data = []
            elif training_data is None:
                training_data = []
            
            logger.debug(f"[LIST] Found {len(training_data)} training items")
            return training_data
        except Exception as e:
            logger.error(f"[ERROR] Failed to get training data: {e}")
            return []
    
    def clear_training_data(self, connection_id: int) -> dict:
        """Clear all training data for a connection."""
        logger.info(f"🗑️ Clearing training data for connection {connection_id}")
        
        result = {
            "success": False,
            "items_removed": 0,
            "errors": []
        }
        
        try:
            vn = self.get_vanna_instance(connection_id)
            
            # Get all training data
            try:
                training_data_raw = vn.get_training_data()
                
                # Convert to list if it's a DataFrame
                if isinstance(training_data_raw, pd.DataFrame):
                    if len(training_data_raw) > 0:
                        training_data = training_data_raw.to_dict('records')
                    else:
                        training_data = []
                elif isinstance(training_data_raw, list):
                    training_data = training_data_raw
                else:
                    training_data = []
                    
            except Exception as e:
                logger.warning(f"[WARNING] Could not retrieve training data: {e}")
                training_data = []
            
            # Remove each training item
            for item in training_data:
                if isinstance(item, dict) and 'id' in item:
                    try:
                        vn.remove_training_data(id=item['id'])
                        result["items_removed"] += 1
                    except Exception as e:
                        error_msg = f"Failed to remove item {item['id']}: {str(e)}"
                        logger.warning(f"[WARNING] {error_msg}")
                        result["errors"].append(error_msg)
            
            result["success"] = True
            logger.info(f"[OK] Training data cleared: {result['items_removed']} items removed")
            
        except Exception as e:
            error_msg = f"Failed to clear training data: {str(e)}"
            logger.error(f"[ERROR] {error_msg}")
            result["errors"].append(error_msg)
        
        return result

    def force_reset_training(self, connection_id: int) -> dict:
        """Force reset training by removing ChromaDB directory."""
        import shutil
        
        logger.info(f"🔥 Force resetting training for connection {connection_id}")
        
        try:
            # Remove from cache
            if connection_id in self.vanna_instances:
                del self.vanna_instances[connection_id]
            
            # Remove cached provider info
            if connection_id in self.connection_providers:
                del self.connection_providers[connection_id]
            
            # Remove ChromaDB directory
            chroma_path = os.path.join(VANNA_CACHE_DIR, f'chroma_db_{connection_id}')
            if os.path.exists(chroma_path):
                shutil.rmtree(chroma_path)
                logger.info(f"[FOLDER] Removed ChromaDB directory: {chroma_path}")
            
            return {
                "success": True,
                "message": f"Training forcefully reset for connection {connection_id}"
            }
            
        except Exception as e:
            logger.error(f"[ERROR] Force reset failed: {e}")
            return {
                "success": False,
                "message": f"Force reset failed: {str(e)}"
            }

# Global instance
vanna_service = VannaService()