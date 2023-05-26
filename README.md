# QRCode Visualizer

## About Project

Most QR code reader programs are designed to display the address when a URL is detected in the QR Code data and open web browser when clicked.

This has a problem that it is difficult to represent the actual information of the QR Code.

In this project, we aim to express QR Code in real-time to make the information more accessible to users.

iPhone Camera | QRCode Visualizer
:---:|:---:
![iphone_cam](./assets/iphone_cam.jpeg) | ![sample](./assets/sample.png)

## Getting Started

### Prerequisites

```
pip3 -r requirements.txt
```

### Run

```
python3 qrcode_visualizer.py
```

- Calibrate camera if no `calibration_result.npz` exists
- Visualize qrcode!


## Features

### Web Page


https://github.com/imssm99/qrcode-visualizer/assets/15193055/5ffde759-1218-4180-8cad-4fa78d7436b6


### 3D Object


https://github.com/imssm99/qrcode-visualizer/assets/15193055/82122f7e-2bb5-4870-b35e-c42b189e5c5b


### Memo


https://github.com/imssm99/qrcode-visualizer/assets/15193055/bea05b4b-0d74-4f36-a61e-96b5cd01a354


## Background

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

## Dependencies

- Written in [Python3](https://www.python.org)
- [OpenCV](https://opencv.org) for capture and process video
- [Selenium](https://www.selenium.dev) for render web page

## References

- [mint-lab/cv_tutorial](https://github.com/mint-lab/cv_tutorial)
