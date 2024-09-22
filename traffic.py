import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def simulate():
    try:
        N_lane = int(entry_N_lane.get())
        if N_lane not in [2, 4]:
            result_label.config(text="Jumlah jalur harus 2 atau 4.")
            return
        L = float(entry_L.get())
        D_mean = float(entry_D_mean.get())
        D_std = float(entry_D_std.get())
        delta_t_mean = float(entry_delta_t_mean.get())
        delta_t_std = float(entry_delta_t_std.get())
        a_mean = float(entry_a_mean.get())
        a_std = float(entry_a_std.get())
        v_max = float(entry_vmax.get())
        T_green = float(entry_Tgreen.get())
        D_gap_threshold = float(entry_D_gap.get())
    except ValueError:
        result_label.config(text="Masukkan nilai numerik yang valid.")
        return

    num_cars_per_lane = 50  # jumlah maksimum mobil per jalur
    times = np.linspace(0, T_green, 1000)  # waktu simulasi

    # data mobil per jalur
    cars_data = {}

    for lane in range(N_lane):
        delta_t_i = np.random.normal(delta_t_mean, delta_t_std, num_cars_per_lane)
        delta_t_i = np.maximum(delta_t_i, 0.5)  # waktu reaksi minimum 0.5 detik
        a_i = np.random.normal(a_mean, a_std, num_cars_per_lane)
        a_i = np.maximum(a_i, 1)  # percepatan minimum 1 m/s²
        D_i = np.random.normal(D_mean, D_std, num_cars_per_lane)
        D_i = np.maximum(D_i, 1)  # jarak minimum 1 meter

        cars_data[lane] = {
            'delta_t_i': delta_t_i,
            'a_i': a_i,
            'D_i': D_i,
            's_i': [],
            't_i': [],
            'crossed': [],
            'overtaken': [],
            'lane_changes': []
        }

    # simulasi pergerakan mobil
    max_positions = []
    for lane in range(N_lane):
        lane_data = cars_data[lane]
        delta_t_i = lane_data['delta_t_i']
        a_i = lane_data['a_i']
        D_i = lane_data['D_i']

        s_i_list = []
        t_i_list = []
        crossed_list = []

        for i in range(num_cars_per_lane):
            current_lane = lane
            lane_changes = []

            # waktu mulai bergerak
            if i == 0:
                t_i = 0
            else:
                t_i = t_i_list[i - 1] + delta_t_i[i - 1]

            t_i_list.append(t_i)

            # Posisi Awal
            if i == 0:
                s_i0 = -(L)
            else:
                s_i0 = s_i_list[i - 1][0] - (L + D_i[i - 1])

            # waktu mencapai v_max
            t_v = t_i + v_max / a_i[i]

            # posisi saat mencapai v_max
            s_v = s_i0 + 0.5 * a_i[i] * (t_v - t_i) ** 2

            # fungsi posisi mobil ke-i
            s_i = []
            current_lane_list = []
            overtaken = False
            for idx, t in enumerate(times):
                if t < t_i:
                    s = s_i0
                elif t_i <= t < t_v:
                    s = s_i0 + 0.5 * a_i[i] * (t - t_i) ** 2
                else:
                    s = s_v + v_max * (t - t_v)

                # car crash prevention logic
                if i > 0 and len(s_i_list[i - 1]) > idx:
                    # check distance to the car in front
                    distance_to_front_car = s_i_list[i - 1][idx] - s
                    if distance_to_front_car < 7:  # if too close, slow down or stop
                        s = s_i_list[i - 1][idx] - 7

                # TODO: Overtaking logic

                s_i.append(s)
                current_lane_list.append(current_lane)

            s_i = np.array(s_i)
            s_i_list.append(s_i)
            lane_data['lane_changes'].append(lane_changes)
            max_positions.append(max(s_i))

            # cek apakah mobil melewati persimpangan
            crossed = np.where(s_i >= 0)[0]
            if len(crossed) > 0:
                t_cross = times[crossed[0]]
                if t_cross <= T_green:
                    crossed_list.append((i, t_cross))
                else:
                    break
            else:
                break

        lane_data['s_i'] = s_i_list
        lane_data['t_i'] = t_i_list
        lane_data['crossed'] = crossed_list

    # menghitung total mobil yang melewati persimpangan
    total_cars_passed = sum(len(cars_data[lane]['crossed']) for lane in cars_data)
    result_label.config(text=f"{total_cars_passed} mobil melewati persimpangan.", justify=tk.LEFT)

    # plot hasil awal
    ax.clear()
    traffic_ax.clear()
    colors = ['black', 'green', 'orange', 'purple']
    car_rects_by_lane = [[] for _ in range(N_lane)]

    max_position = max(max_positions) if max_positions else 200  # get the max position across all cars
    for lane in range(N_lane):
        lane_data = cars_data[lane]
        s_i_list = lane_data['s_i']
        lane_changes_list = lane_data['lane_changes']
        for idx, s_i in enumerate(s_i_list):
            if idx >= 25:  # batasi visualisasi hingga 25 mobil per jalur
                break

            # plot trajectory in the main graph
            lane_changes = lane_changes_list[idx]
            if lane_changes:
                # plot before lane change
                change_idx = np.where(times >= lane_changes[0][0])[0][0]
                ax.plot(times[:change_idx], s_i[:change_idx], '-', color=colors[lane])
                # red dot at lane change
                ax.plot(times[change_idx], s_i[change_idx], 'ro')
                # plot after lane change
                new_lane = lane_changes[0][2]
                ax.plot(times[change_idx:], s_i[change_idx:], '-', color=colors[new_lane])
            else:
                ax.plot(times, s_i, '-', color=colors[lane])

            # draw rectangle for each car in the lane visualization graph
            if len(s_i) > 0:
                car_position = s_i[0]  # initial position at t=0
                car_rect = patches.Rectangle((lane * 7, car_position), 0.4, 5, edgecolor='black', facecolor='gray')
                traffic_ax.add_patch(car_rect)
                car_rects_by_lane[lane].append({'rect': car_rect, 'idx': idx})

    ax.axhline(0, color='red', linestyle='--', label='Persimpangan')
    ax.set_title('Pergerakan Mobil Saat Lampu Hijau')
    ax.set_xlabel('Waktu (s)')
    ax.set_ylabel('Posisi (m)')
    ax.set_ylim([-50, max_position + 50])  # memperluas sumbu y hingga -50 meter
    ax.legend()
    ax.grid(True)

    # visualize traffic lanes with switched axes
    traffic_ax.set_ylim([-50, max_position + 50])  # show from -50 to max position
    traffic_ax.set_xlim([-2, N_lane * 7])
    traffic_ax.axhline(0, color='red', linestyle='--')  # red dotted horizontal line at y=0
    traffic_ax.set_ylabel("Posisi (m)")
    traffic_ax.set_xlabel("Jalur")
    traffic_ax.set_title("Visualisasi Lalu Lintas")
    traffic_ax.set_xticks([i * 7 + 1 for i in range(N_lane)])
    traffic_ax.set_xticklabels([f"Jalur {i+1}" for i in range(N_lane)])

    canvas.draw()
    traffic_canvas.draw()

    def update_traffic_display(x_hover):
        """Update the traffic lane view when the user hovers over the graph."""
        for lane in range(N_lane):
            lane_data = cars_data[lane]
            s_i_list = lane_data['s_i']
            lane_changes_list = lane_data['lane_changes']
            for car_info in car_rects_by_lane[lane]:
                idx = car_info['idx']
                car_rect = car_info['rect']
                if idx < len(s_i_list):
                    s_i = s_i_list[idx]
                    if len(s_i) > 0:
                        # update the car's position at the current hovered time
                        t_idx = (np.abs(times - x_hover)).argmin()  # get the nearest time index
                        new_position = s_i[t_idx]

                        # check if the car has changed lanes
                        current_lane = lane
                        for change in lane_changes_list[idx]:
                            if x_hover >= change[0]:
                                current_lane = change[2]
                            else:
                                break

                        car_rect.set_xy((current_lane * 7, new_position))

        traffic_canvas.draw()

    # function to handle mouse motion and update hover line and traffic state
    def on_hover(event):
        if event.xdata is None:
            return
        # update vertical hover line
        x_hover = event.xdata
        hover_line.set_xdata(x_hover)
        canvas.draw()

        # update the traffic display to reflect car positions at the hovered time
        update_traffic_display(x_hover)

    # add hover event to update vertical line and traffic lane visualization
    hover_line = ax.axvline(color='red', linestyle='--')  # vertical line for hover
    canvas.mpl_connect("motion_notify_event", on_hover)


# GUI
root = tk.Tk()
root.title("Simulasi Jumlah Mobil Melewati Persimpangan Multijalur")

# grid untuk tata letak
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.columnconfigure(2, weight=1)

frame_input = ttk.Frame(root)
frame_input.grid(row=0, column=0, sticky='nw', padx=10, pady=10)

# meningkatkan ukuran font dan bold
style = ttk.Style()
style.configure('TLabel', font=('TkDefaultFont', 10, 'bold'))
style.configure('TEntry', font=('TkDefaultFont', 10))
style.configure('TButton', font=('TkDefaultFont', 10, 'bold'))
style.configure('TFrame', padding=(5, 5))

fields = [
    ("Jumlah Jalur (2 atau 4):", "2"),
    ("Panjang Mobil (m):", "5"),
    ("Jarak Antar Mobil Rata-Rata (m):", "2"),
    ("Standar Deviasi Jarak (m):", "0.5"),
    ("Waktu Reaksi Rata-Rata (s):", "1"),
    ("Standar Deviasi Waktu Reaksi (s):", "0.2"),
    ("Percepatan Rata-Rata (m/s²):", "2"),
    ("Standar Deviasi Percepatan (m/s²):", "0.5"),
    ("Kecepatan Maksimum (m/s):", "13.89"),
    ("Durasi Lampu Hijau (s):", "15"),
    ("Ambang Perpindahan Jalur (m):", "5")
]

entries = []

for i, (label_text, default_value) in enumerate(fields):
    ttk.Label(frame_input, text=label_text).grid(row=i, column=0, sticky=tk.W, pady=2)
    entry = ttk.Entry(frame_input)
    entry.insert(0, default_value)
    entry.grid(row=i, column=1, pady=2)
    entries.append(entry)

(entry_N_lane,
 entry_L,
 entry_D_mean,
 entry_D_std,
 entry_delta_t_mean,
 entry_delta_t_std,
 entry_a_mean,
 entry_a_std,
 entry_vmax,
 entry_Tgreen,
 entry_D_gap) = entries

# Tombol Simulasi
simulate_button = ttk.Button(frame_input, text="Simulasikan", command=simulate)
simulate_button.grid(row=len(fields), column=0, columnspan=2, pady=10)

result_label = ttk.Label(frame_input, text="")
result_label.grid(row=len(fields) + 1, column=0, columnspan=2)

frame_plot = ttk.Frame(root)
frame_plot.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)
root.rowconfigure(0, weight=1)
root.columnconfigure(1, weight=1)

fig, ax = plt.subplots(figsize=(8, 6))
canvas = FigureCanvasTkAgg(fig, master=frame_plot)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

# traffic visualization plot area
frame_traffic = ttk.Frame(root)
frame_traffic.grid(row=0, column=2, sticky='nsew', padx=10, pady=10)
traffic_fig, traffic_ax = plt.subplots(figsize=(8, 6))
traffic_canvas = FigureCanvasTkAgg(traffic_fig, master=frame_traffic)
traffic_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

root.mainloop()
