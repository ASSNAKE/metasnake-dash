import dash, os
from dash import html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
from assnake.core.Dataset import Dataset

# Initialize Dash app
app = dash.Dash(__name__)

# Function to fetch datasets (to be implemented)
def get_datasets_from_file_system():
    datasets = [d['df'] for d in Dataset.list_in_db().values()]
    return datasets


def get_sample_sets(selected_dataset, fs_prefix):
    sample_sets_dir = os.path.join(fs_prefix, selected_dataset, 'sample_sets')
    sample_sets = []

    # Check if the directory exists
    if os.path.exists(sample_sets_dir) and os.path.isdir(sample_sets_dir):
        # Iterate over each subdirectory in the directory
        for dir_name in os.listdir(sample_sets_dir):
            dir_path = os.path.join(sample_sets_dir, dir_name)
            if os.path.isdir(dir_path):
                # Iterate over each file in the subdirectory
                for file_name in os.listdir(dir_path):
                    if file_name.endswith('.tsv'):
                        sample_set_name = dir_name.split('_')[0]  # Extract the sample set name from the directory name
                        sample_set_name = dir_path.split('/')[-1] 
                        print(dir_path)
                        if sample_set_name not in sample_sets:
                            sample_sets.append(sample_set_name)

    return sample_sets


def get_reads_data(selected_dataset, selected_sample_set, fs_prefix):
    # Construct the path to the reads_and_basepairs.tsv file
    file_path = os.path.join(fs_prefix, selected_dataset, 'sample_sets', f"{selected_sample_set}/count/reads_and_basepairs.tsv")
    print(file_path)
    # Check if the file exists
    if os.path.exists(file_path):
        # Read the data from the file
        df = pd.read_csv(file_path, sep='\t')
        return df
    else:
        # Return an empty DataFrame if the file does not exist
        return pd.DataFrame(columns=['Sample', 'Reads', 'BasePairs'])


app.layout = html.Div([
    # Dropdowns
    html.Div([
        dcc.Dropdown(
            id='dataset-dropdown',
            options=[{'label': ds, 'value': ds} for ds in get_datasets_from_file_system()],
            value='Dataset1'  
        ),
        dcc.Dropdown(
            id='sample-set-dropdown',
        ),
    ]),

    # First row: Reads Barplot
    html.Div([
        dcc.Graph(id='reads-chart', style={'width': '100%'})
    ], style={'width': '100%', 'display': 'flex'}),

    # Second row: Histogram and Boxplot
    html.Div([
        # Histogram
        html.Div([
            dcc.Graph(id='reads-histogram')
        ], style={'width': '50%'}),

        # Boxplot
        html.Div([
            dcc.Graph(id='reads-boxplot')
        ], style={'width': '50%'})
    ], style={'display': 'flex', 'flex-wrap': 'wrap'})
], style={'padding': '10px'})



# Callback to update sample set dropdown based on selected dataset
@app.callback(
    Output('sample-set-dropdown', 'options'),
    Input('dataset-dropdown', 'value')
)
def update_sample_set_dropdown(selected_dataset):
    dataset = Dataset(selected_dataset)
    sample_sets = get_sample_sets(selected_dataset, dataset.fs_prefix)
    return [{'label': ss, 'value': ss} for ss in sample_sets]

# Callback to update reads chart based on selected sample set and dataset
@app.callback(
    Output('reads-chart', 'figure'),
    [Input('dataset-dropdown', 'value'),
     Input('sample-set-dropdown', 'value')]
)
def update_reads_chart(selected_dataset, selected_sample_set):
    if not selected_dataset or not selected_sample_set:
        return dash.no_update  # Return no update if either dropdown is not selected
    
    dataset = Dataset(selected_dataset)

    df = get_reads_data(selected_dataset, selected_sample_set, dataset.fs_prefix)
    df_sorted = df.sort_values(by='Reads', ascending=True) 

    fig = px.bar(df_sorted, x='Sample', y='Reads') 
    fig.update_layout(title=f'Bar plot of number of reads for dataset {selected_dataset}')

    return fig


@app.callback(
    Output('reads-histogram', 'figure'),
    [Input('dataset-dropdown', 'value'),
     Input('sample-set-dropdown', 'value')]
)
def update_reads_histogram(selected_dataset, selected_sample_set):
    if not selected_dataset or not selected_sample_set:
        return dash.no_update

    dataset = Dataset(selected_dataset)
    df = get_reads_data(selected_dataset, selected_sample_set, dataset.fs_prefix)
    fig = px.histogram(df, x='Reads', nbins=50) 
    fig.update_layout(title=f'Hist plot of number of reads for dataset {selected_dataset}')

    return fig


@app.callback(
    Output('reads-boxplot', 'figure'),
    [Input('dataset-dropdown', 'value'),
     Input('sample-set-dropdown', 'value')]
)
def update_reads_boxplot(selected_dataset, selected_sample_set):
    if not selected_dataset or not selected_sample_set:
        return dash.no_update

    dataset = Dataset(selected_dataset)
    df = get_reads_data(selected_dataset, selected_sample_set, dataset.fs_prefix)
    data = go.Violin(y=df['Reads'],  points='all', pointpos=0, box_visible=True)  
    fig = go.Figure(data=data)
    fig.update_layout(title=f'Violin plot of number of reads for dataset {selected_dataset}')

    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')