# ✨ Mouse Path Tracer

**Mouse Path Tracer** is a high-performance desktop utility built with Python that captures, visualizes, and exports your mouse movements into smooth, high-quality video animations. Whether you are creating tutorials, analyzing gaming patterns, or generating digital art from your workflows, this tool provides a professional interface for path tracing.

## 🚀 Features

* **Real-time Capture**: Record mouse paths across multiple monitors at custom sample rates (up to 120Hz).
* **Dynamic Visualizer**: Watch your path grow in real-time on a DPI-aware preview canvas.
* **Customizable Aesthetics**:
* Change path colors and line thickness.
* Toggle path "dots" for granular movement visibility.
* Use solid color backgrounds or upload custom images.


* **Video Export**: Save your recordings as `.mp4` files with adjustable playback speeds (0.1x to 10.0x).
* **Global Hotkeys**: Start and stop recordings instantly using the **F8** key, even when the app is minimized.

## 📖 How to Use

1. **Select Display**: Choose which monitor you want to record from the "Display" dropdown.
2. **Customize Style**: Set your preferred line color, thickness, and background.
3. **Record**:
* Click **"Start Recording"** or press **F8**.
* Move your mouse. The path will appear on the preview canvas.
* Click **"Stop Recording"** or press **F8** again.

4. **Export**: Adjust the playback speed (e.g., 2.0x for a time-lapse) and click **"Export Video"** to save your `.mp4`.

## 💻 Developer Notes

* **High-DPI Support**: The app includes a Windows-specific fix (`ctypes.windll`) to ensure the UI and mouse coordinates remain sharp and accurate on 4K displays.
* **Multithreading**: The tracking loop runs on a background thread to ensure the GUI remains responsive during long recording sessions.

## 📜 License

This project is provided "as-is" for creative and analytical use.