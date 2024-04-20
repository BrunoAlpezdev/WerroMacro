import tkinter as tk
from tkinter import filedialog
from tkinter import scrolledtext
from pynput.mouse import Controller as MouseController, Button as MouseButton
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Listener as MouseListener
from pynput import mouse, keyboard
import time
import json

class MouseKeyboardRecorder(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Replicador de Acciones')

        # Historial de acciones
        self.action_history = scrolledtext.ScrolledText(self, wrap=tk.WORD)
        self.action_history.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.last_move_time = 0  # Inicializa la última vez que se registró un movimiento
        self.move_interval = 0.3
        
        # Controles para repetir y delay
        repeat_frame = tk.Frame(self)
        repeat_frame.pack(padx=10, pady=5, fill=tk.X)

        tk.Label(repeat_frame, text='repetir').pack(side=tk.LEFT)
        self.repeat_count = tk.Entry(repeat_frame, width=5)
        self.repeat_count.pack(side=tk.LEFT, padx=5)
        self.repeat_infinite = tk.Checkbutton(repeat_frame, text='infinito')
        self.repeat_infinite.pack(side=tk.LEFT, padx=5)
        tk.Label(repeat_frame, text='delay').pack(side=tk.LEFT)
        self.delay_entry = tk.Entry(repeat_frame, width=5)
        self.delay_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(repeat_frame, text='segundos').pack(side=tk.LEFT)

        # Botón Replicar Grabación
        self.replicate_button = tk.Button(self, text='Replicar Grabación', command=self.replicate)
        self.replicate_button.pack(pady=10)

        # Botones Grabar, Subir  y Guardar Grabación
        recording_frame = tk.Frame(self)
        recording_frame.pack(padx=10, pady=5, fill=tk.X)
        self.save_button = tk.Button(self, text='Guardar Grabación', command=self.save_recording)
        self.save_button.pack(pady=5)

        self.record_button = tk.Button(recording_frame, text='Grabar', command=self.start_recording)
        self.record_button.pack(side=tk.LEFT, padx=5)
        self.upload_button = tk.Button(recording_frame, text='Subir Grabación', command=self.upload_recording)
        self.upload_button.pack(side=tk.LEFT, padx=5)

        # Etiqueta para el archivo de grabación
        self.recording_label = tk.Label(self, text='Ningún archivo de grabación cargado')
        self.recording_label.pack(pady=5)

        # Configuración del listener del mouse y teclado
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        self.mouse_listener = MouseListener(on_move=self.on_move, on_click=self.on_click)
        # Variables para control de grabación
        self.recording = False
        self.events = []
        

    def start_recording(self):
        if not self.recording:
            self.events = []
            self.action_history.delete(1.0, tk.END)
            self.recording = True
            self.mouse_listener.start()
            self.keyboard_listener.start()
            self.record_button.config(text='Detener Grabación', command=self.stop_recording)

    def stop_recording(self):
        if self.recording:
            # Detiene la grabación primero
            self.recording = False

            # Después detiene los listeners
            self.mouse_listener.stop()
            self.keyboard_listener.stop()

            # Elimina el último evento, que debería ser el clic para detener la grabación
            if self.events:  # Asegurarse de que hay eventos para eliminar
                self.events.pop()
                self.events.pop()

            self.record_button.config(text='Grabar', command=self.start_recording)

    def upload_recording(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.recording_label.config(text=f'Archivo de grabación cargado: {file_path}')
            # Aquí cargarías el archivo y actualizarías el historial de acciones.
            
    def save_recording(self):
        if not self.events:
            tk.messagebox.showwarning("Guardar Grabación", "No hay ninguna grabación para guardar.")
            return
        
        #eliminar los releases de los eventos
        filtered_events = [e for e in self.events if not (e['type'] == 'click' and not e['pressed'])]
        
        file_path = filedialog.asksaveasfilename(defaultextension='.json',
                                                 filetypes=[('JSON files', '*.json'), ('All files', '*.*')],
                                                 title="Guardar grabación como...")
        if not file_path:
            return  # El usuario canceló la operación de guardar

        with open(file_path, 'w') as outfile:
            json.dump(filtered_events, outfile) #pasar los eventos limpios
        self.recording_label.config(text=f'Grabación guardada en: {file_path}')

    def replicate(self):
        # Carga los eventos desde un archivo JSON
        file_path = filedialog.askopenfilename(filetypes=[('JSON files', '*.json')])
        if not file_path:
            return  # El usuario canceló la operación
        
        with open(file_path, 'r') as json_file:
            events = json.load(json_file)
            
        mouse_controller = MouseController()
        keyboard_controller = KeyboardController()
        
        start_time = events[0]['time']  # Tiempo del primer evento
        
        for event in events:
            current_time = event['time']
            delay = current_time - start_time  # Calcula el retraso desde el evento anterior
            time.sleep(delay)  # Pausa la ejecución para simular el tiempo real
            start_time = current_time  # Actualiza el tiempo de inicio para el próximo ciclo
            if event['type'] == 'click':
                # Obtiene la información del evento
                x, y = event['pos']
                button = MouseButton.left if event['button'] == 'Button.left' else MouseButton.right
                pressed = event['pressed']
                
                # Mueve el mouse y hace clic o suelta
                mouse_controller.position = (x, y)
                mouse_controller.press(button)
            elif event['type'] == 'keypress':
                # Obtiene la tecla del evento
                key = event['key']
                try:
                    # Intenta interpretar la tecla como una tecla especial
                    key_to_press = getattr(Key, key)
                except AttributeError:
                    # Si no es una tecla especial, es un caracter
                    key_to_press = key
                
                # Presiona y suelta la tecla
                keyboard_controller.press(key_to_press)
                keyboard_controller.release(key_to_press)
            elif event['type'] == 'move':
                x, y = event['pos']
                mouse_controller.position = (x, y)
                

            # Añade un delay entre ciclos si se requiere
            #if self.delay_entry == '' or self.delay_entry == 0:
            #    delay = 0.0
            #else:
            #    delay = float(self.delay_entry.get())
                
            time.sleep(delay)
        
    def on_move(self, x, y):
        current_time = time.time()
        if self.recording and (current_time - self.last_move_time >= self.move_interval):
            event = {
                'type': 'move',
                'pos': (x, y),
                'time': current_time  # Captura el tiempo actual
            }
            self.events.append(event)
            self.last_move_time = current_time  # Actualiza el tiempo del último evento registrado

    def on_click(self, x, y, button, pressed):
        if self.recording:
            event = {
                'type': 'click',
                'pos': (x, y),
                'button': str(button),
                'pressed': pressed,
                'time': time.time()  # Captura el tiempo actual
            }
            self.events.append(event)
            action = f"Mouse {'Pressed' if pressed else 'Released'} at ({x}, {y}), button={button}"
            self.action_history.insert(tk.END, action + "\n")
            
    def on_press(self, key):
        if self.recording:
            # Convertimos el objeto key a un formato adecuado antes de guardar
            try:
                key_data = key.char  # intentamos obtener el caracter de la tecla
            except AttributeError:
                key_data = str(key)  # para teclas especiales, convertimos a string
            
            event = {
                'type': 'keypress', 
                'key': key_data
            }
            self.events.append(event)
            self.action_history.insert(tk.END, f"Key pressed: {key_data}\n")
            
if __name__ == "__main__":
    app = MouseKeyboardRecorder()
    app.mainloop()