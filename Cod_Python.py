import math
import re
import os
import tkinter as tk

root = None
canvas = None
lbl = None

def Testare_automata(cale_fisier_referinta, cale_fisier_dinamic):
    global root, canvas, lbl

    try:
        cale_ref = str(cale_fisier_referinta).strip()
        cale_din = str(cale_fisier_dinamic).strip()

        def extrage_date_curate(cale_fisier):
            if not os.path.exists(cale_fisier):
                return None, None

            with open(cale_fisier, 'r', encoding='utf-8') as f:
                continut = f.read()

            text_curat = re.sub(r'\[.*?\]', '', continut)
            pattern_data = r'\d{1,2}:\d{2}:\d{2}\.\d{1,4}\s+[AP]M\s+\d{1,2}/\d{1,2}/\d{4}'

            blocuri = re.split(pattern_data, text_curat)
            ore = re.findall(pattern_data, text_curat)

            if not ore:
                return None, None

            for bloc in reversed(blocuri):
                if "LED Forward Voltage" in bloc:
                    ultima_citire = bloc.replace('\n', ' ').replace('\r', ' ')
                    break
            else:
                ultima_citire = blocuri[-1].replace('\n', ' ').replace('\r', ' ')

            ultima_ora = ore[-1]
            return ultima_citire, ultima_ora

        date_ref, _ = extrage_date_curate(cale_ref)
        date_din, ora_dinamica = extrage_date_curate(cale_din)

        if not date_ref or not date_din:
            return "Eroare: Lipsa date in fisiere"

        def parseaza(text):
            rez = {}

            parametri = [
                "LED Forward Voltage",
                "Duty Cycle (setpoint)",
                "Duty Cycle (LED)",
                "Circuit Current",
                "Reference Resistor",
                "LED Detected",
                "Detected LED Color"
            ]

            for param in parametri:
                start_idx = text.find(param)

                if start_idx != -1:
                    val_si_rest = text[start_idx + len(param):].strip()

                    for other_param in parametri:
                        if other_param != param:
                            idx = val_si_rest.find(other_param)
                            if idx != -1:
                                val_si_rest = val_si_rest[:idx]

                    valoare = re.sub(r'[:;|=\s\t,]+', ' ', val_si_rest).strip()
                    rez[param] = valoare

            return rez

        dict_ref = parseaza(date_ref)
        dict_din = parseaza(date_din)

        greutate_w = 500.0
        culoare_linie = "#FF0000"
        titlu_led = "RED LED"

        try:
            v_real = float(dict_din.get("LED Forward Voltage", "0").split()[0])
            i_real = float(dict_din.get("Circuit Current", "0").split()[0])

            culoare_detectata = dict_din.get(
                "LED Detected",
                dict_din.get("Detected LED Color", "LED Not Detected")
            ).strip()

            if v_real > 1.0 and i_real > 0.1 and "Not Detected" not in culoare_detectata:

                if "Yellow" in culoare_detectata:
                    culoare_linie = "#FFCC00"
                    titlu_led = "YELLOW LED"
                    tensiune_prag = 1.76
                else:
                    culoare_linie = "#FF0000"
                    titlu_led = "RED LED"
                    tensiune_prag = 1.66

                factor_p = 2.5

                if v_real > tensiune_prag:
                    greutate_w = i_real / math.pow(v_real - tensiune_prag, factor_p)
                else:
                    greutate_w = 500.0

                v_limita_grafic = 2.6
                i_limita_grafic = 30.0

                puncte = []

                for pas in range(0, 261):
                    v_sim = (pas / 260.0) * v_limita_grafic

                    if v_sim < tensiune_prag:
                        i_sim = 0.005 * v_sim
                    else:
                        i_sim = greutate_w * math.pow(v_sim - tensiune_prag, factor_p)

                    puncte.append((v_sim, i_sim))

                if root is None or not tk.Toplevel.winfo_exists(root):
                    root = tk.Tk()
                    root.title("LED I-V Characteristic")
                    root.geometry("570x470")
                    root.configure(bg="#F5F5F5")
                    root.protocol("WM_DELETE_WINDOW", lambda: None)

                    lbl = tk.Label(
                        root,
                        text="",
                        font=("Arial", 11, "bold"),
                        bg="#F5F5F5",
                        fg="#333333"
                    )
                    lbl.pack(pady=12)

                    canvas = tk.Canvas(
                        root,
                        width=510,
                        height=340,
                        bg="white",
                        highlightthickness=1,
                        highlightbackground="#CCCCCC"
                    )
                    canvas.pack()

                canvas.delete("all")

                lbl.config(
                    text=f"{titlu_led} I-V Characteristic\n"
                         f"Operating Point: {v_real:.3f} V | {i_real:.3f} mA"
                )

                x0 = 70
                y0 = 270
                x_max = 470
                y_top = 35

                canvas.create_line(x0, y0, x_max, y0, width=2, fill="#333333", arrow=tk.LAST)
                canvas.create_line(x0, y0, x0, y_top, width=2, fill="#333333", arrow=tk.LAST)

                canvas.create_text(
                    270,
                    320,
                    text="Voltage U (V)",
                    font=("Arial", 13, "bold"),
                    fill="#333333"
                )

                canvas.create_text(
                    25,
                    155,
                    text="Current I (mA)",
                    font=("Arial", 13, "bold"),
                    fill="#333333",
                    angle=90
                )

                valori_axa_y = [0, 5, 10, 15, 20, 25, 30]

                for val_i in valori_axa_y:
                    y_pos = y0 - (val_i / i_limita_grafic) * 210
                    canvas.create_line(x0 - 5, y_pos, x0, y_pos, fill="#333333", width=1.5)
                    canvas.create_text(
                        x0 - 24,
                        y_pos,
                        text=f"{val_i}",
                        font=("Arial", 9, "bold"),
                        fill="#333333"
                    )

                valori_axa_x = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6]

                for val_v in valori_axa_x:
                    x_pos = x0 + (val_v / v_limita_grafic) * 390
                    canvas.create_line(x_pos, y0, x_pos, y0 + 5, fill="#333333", width=1.5)
                    canvas.create_text(
                        x_pos,
                        y0 + 18,
                        text=f"{val_v:.1f}",
                        font=("Arial", 8, "bold"),
                        fill="#333333"
                    )

                pixel_puncte = []

                for v_p, i_p in puncte:
                    x = x0 + (v_p / v_limita_grafic) * 390
                    y = y0 - (i_p / i_limita_grafic) * 210

                    if x <= x_max and y >= y_top:
                        pixel_puncte.append((x, y))

                for i in range(len(pixel_puncte) - 1):
                    canvas.create_line(
                        pixel_puncte[i][0],
                        pixel_puncte[i][1],
                        pixel_puncte[i + 1][0],
                        pixel_puncte[i + 1][1],
                        fill=culoare_linie,
                        width=3
                    )

                x_real = x0 + (v_real / v_limita_grafic) * 390
                y_real = y0 - (i_real / i_limita_grafic) * 210

                canvas.create_oval(
                    x_real - 6,
                    y_real - 6,
                    x_real + 6,
                    y_real + 6,
                    fill="#00FF00",
                    outline="black",
                    width=2
                )

                canvas.create_text(
                    x_real + 70,
                    y_real - 12,
                    text="Measured Point",
                    font=("Arial", 9, "bold"),
                    fill="black"
                )

                root.update_idletasks()
                root.update()

        except:
            pass

        identice, diferente = [], []

        chei_ordonate = [
            "LED Forward Voltage",
            "Duty Cycle (setpoint)",
            "Duty Cycle (LED)",
            "Circuit Current",
            "Reference Resistor"
        ]

        cheia_culoare = "LED Detected" if "LED Detected" in dict_din else "Detected LED Color"
        chei_ordonate.append(cheia_culoare)

        for k in chei_ordonate:
            val_r = dict_ref.get(k, "N/A")
            val_d = dict_din.get(k, "N/A")

            try:
                num_r_match = re.findall(r"[-+]?\d*\.\d+|\d+", val_r)
                num_d_match = re.findall(r"[-+]?\d*\.\d+|\d+", val_d)

                if num_r_match and num_d_match:
                    vr_num = float(num_r_match[0])
                    vd_num = float(num_d_match[0])

                    # S-a trecut la o marja ABSOLUTA fixa de 0.1 unitati
                    if abs(vr_num - vd_num) <= 0.1:
                        identice.append(f"{k}: {vd_num:.4f}")
                    else:
                        diferente.append(f"{k}: {vr_num:.4f} vs {vd_num:.4f}")
                else:
                    if val_r.lower() == val_d.lower() or val_r.split()[0].lower() in val_d.lower():
                        identice.append(f"{k}: {val_d}")
                    else:
                        diferente.append(f"{k}: {val_r} vs {val_d}")

            except:
                if str(val_r).strip() == str(val_d).strip():
                    identice.append(f"{k}: {val_d}")
                else:
                    diferente.append(f"{k}: {val_r} vs {val_d}")

        res = f"[{ora_dinamica}] "

        if identice:
            res += "TRECUT: " + " | ".join(identice)

        if diferente:
            if "TRECUT" in res:
                res += "   ///   "
            res += "PICAT: " + " | ".join(diferente)

        return res

    except Exception as e:
        return f"Eroare Script Python: {str(e)}"