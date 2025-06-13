# plot_module.py

import csv
import os
import matplotlib.pyplot as plt
from statistics import quantiles
from datetime import datetime
import matplotlib.dates as mdates
from statistics import mean

def aggregate(values, timestamps):
    n = len(values)
    group_size = max(1, n // 100)  # avoid zero division

    values_agg = [mean(values[i:i+group_size]) for i in range(0, n, group_size)]

    timestamps_agg = []
    for i in range(0, n, group_size):
        group = timestamps[i:i+group_size]
        mid_idx = len(group) // 2
        timestamps_agg.append(group[mid_idx])

    return values_agg, timestamps_agg

def read_csv(file_path):
    try:
        with open(file_path, newline='') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            if headers is None:
                return None

            headers_set = set(h.strip().lower() for h in headers)

            if headers_set == {'watt'}:
                watt = [float(row['watt']) for row in reader if row.get('watt')]
                return {'type': 'watt_only', 'data': watt, 'label': os.path.basename(file_path)}

            elif {'timestamp', 'response', 'pods', 'watt'}.issubset(headers_set):
                timestamps, watts, responses, pods, req_counts = [], [], [], [], []
                for row in reader:
                    try:
                        ts = float(row['timestamp'])
                        if ts > 1e12:
                            ts = ts / 1000
                        timestamps.append(datetime.fromtimestamp(ts))
                        watts.append(float(row['watt']))
                        responses.append(float(row['response']))
                        pods.append(int(row['pods']))
                        req_counts.append(int(row['request_count']) if 'request_count' in row and row['request_count'] else None)
                    except (ValueError, KeyError):
                        continue
                return {
                    'type': 'full',
                    'timestamps': timestamps,
                    'watt': watts,
                    'response': responses,
                    'pods': pods,
                    'request_count': req_counts,
                    'label': os.path.basename(file_path)
                }
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return None

def plot_all_subplots(data):
    label = data.get('label', 'output')
    plots_to_draw = []

    if data['type'] == 'watt_only':
        plots_to_draw = ['watt']
    elif data['type'] == 'full':
        plots_to_draw = ['watt', 'pods', 'response']

    num_plots = len(plots_to_draw)
    if num_plots == 0:
        print(f"No valid data to plot for {label}")
        return

    fig, axs = plt.subplots(num_plots, 1, figsize=(10, 4 * num_plots), constrained_layout=True)
    if num_plots == 1:
        axs = [axs]

    i = 0
    if 'watt' in plots_to_draw:
        ax = axs[i]
        if data['type'] == 'full':
            ax.plot(data['timestamps'], data['watt'], label='Watt')
            a_watt, a_timestamps = aggregate(data['watt'], data['timestamps'])
            ax.plot(a_timestamps, a_watt, label='Aggregated watt')
            ax.set_xlabel('Time')
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        else:
            ax.plot(range(len(data['data'])), data['data'], label='Watt')
            ax.set_xlabel('Index')
        ax.set_ylabel('Watt')
        ax.set_title('Watt over Time / Index')
        ax.grid(True)
        i += 1

    if 'response' in plots_to_draw:
        responses = data['response']
        if responses and len(responses) >= 20:
            sorted_resp = sorted(responses)
            try:
                p95 = quantiles(sorted_resp, n=100)[94]
                tail = [r for r in responses if r >= p95]
                if tail:
                    ax = axs[i]
                    ax.plot(range(len(tail)), tail, color='purple')
                    ax.set_title('Response Time (95th Percentile Tail)')
                    ax.set_xlabel('Index in Tail')
                    ax.set_ylabel('Seconds')
                    ax.grid(True)
                    i += 1
            except IndexError:
                print(f"Skipping response plot for {label}: unable to compute percentile")
        else:
            print(f"Skipping response plot for {label}: not enough data")

    if 'pods' in plots_to_draw or 'request_count' in plots_to_draw:
        pods_available = 'pods' in data
        req_available = any(rc is not None for rc in data.get('request_count', []))
    
        if pods_available or req_available:
            ax_left = axs[i]
            ax_right = ax_left.twinx()
    
            if req_available:
                req_counts = [(ts, rc) for ts, rc in zip(data['timestamps'], data['request_count']) if rc is not None]
                if req_counts:
                    times, counts = zip(*req_counts)
                    ax_left.plot(times, counts, label='Request Count', color='orange')
                    ax_left.set_ylabel('Request Count', color='orange')
                    ax_left.tick_params(axis='y')
    
            if pods_available:
                ax_right.plot(data['timestamps'], data['pods'], label='Pods', color='green')
                ax_right.set_ylabel('Pods', color='green')
                ax_right.tick_params(axis='y')
    
            ax_left.set_title('Pods and Request Count over Time')
            ax_left.set_xlabel('Time')
            ax_left.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax_left.grid(True)
            i += 1
    

    fig.suptitle(f'Plots for {label}', fontsize=14)
    os.makedirs("results", exist_ok=True)
    plt.savefig(f"results/{label.replace('.csv', '.pdf')}")
    plt.savefig(f"results/{label.replace('.csv', '.png')}")
    plt.close(fig)

def plot_from_file(path: str):
    data = read_csv(path)
    if data:
        plot_all_subplots(data)

def plot_from_data(data_list, data_type='full', label='from_data'):
    if data_type == 'watt_only':
        data = {'type': 'watt_only', 'data': data_list, 'label': label}
        plot_all_subplots(data)
    else:
        raise ValueError("Only 'watt_only' type is supported for list input.")

