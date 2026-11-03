# Alin C3 · 阿林机器狗固件

基于 [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) 裁剪而成的单板固件，只保留 **`alin-c3`** 一块板子：
ESP32-C3 跑语音 + 显示，128x64 OLED 当脸（几何眼睛表情），四条舵机腿负责站、坐、走、跳舞。

- 语音对话：ESP-SR 离线唤醒，触摸开始/结束对话，唤醒时自动站起来
- 表情：21 种情绪 + 8 种备用眼神，全部几何绘制，无图片资源
- 动作：站/坐/趴/走/转/招手/伸懒腰/摇摆/挠头等，语音或网页触发
- 灯带：常亮 / 呼吸 / 彩虹 / 流水 / 闪烁，颜色、亮度、速度可调
- 网页控制台：设备联网后打开 `http://<设备IP>/`，长按触摸 1 秒屏幕显示二维码
- 舵机微调：网页里 ±20° 校准，存 NVS，重启不丢

## 硬件

| 部件 | 型号 |
| --- | --- |
| 主控 | ESP32-C3 SuperMini（4MB Flash，无 PSRAM） |
| 麦克风 | INMP441 / ICS43434（I2S） |
| 功放 | MAX98357A（I2S） |
| 喇叭 | 8Ω 2~3W 或 4Ω 2~3W |
| 屏幕 | SH1106 OLED 128x64（I2C，0x3C） |
| 触摸 | TTP223（**必须 3.3V 供电**） |
| 灯带 | WS2812 / WS2812B x4 |
| 舵机 | 180° 舵机 x4（SG90 / MG90S） |

### 引脚

| 功能 | GPIO |
| --- | --- |
| 麦克风 WS / SCK / DIN | 7 / 6 / 5 |
| 喇叭 LRCK / BCLK / DOUT | 4 / 3 / 2 |
| OLED SDA / SCL | 8 / 9 |
| 触摸 + 灯带 DIN（复用） | 0 |
| 左前 / 右前 / 左后 / 右后舵机 | 1 / 10 / 20 / 21 |

> 舵机不要从板子取电（四条同时动超过 1.5A），单独供电并共地。
> GPIO20/21 是 C3 的 UART0 默认脚，插上舵机后请用 USB（Serial/JTAG）看日志。

## 编译

已验证环境：**ESP-IDF v5.5.6**（Windows）。上游同时支持 6.0.x，但本固件按 5.5.6 实测通过。

```powershell
# 在 “ESP-IDF 5.5 PowerShell” 终端里
cd Alin-c3
python scripts/build.py alin-c3
```

产物：`build/merged-binary.bin`（合并镜像，含 bootloader + 分区表 + app + assets）。

## 刷机

**方式一：一键脚本**

```powershell
.\flash.ps1            # 自动找串口 -> 烧录 -> 开监视器
.\flash.ps1 -Port COM5  # 指定串口
```

**方式二：Flash Download Tool / 任意 esptool**

合并镜像烧到 **0x0** 即可：

```powershell
python -m esptool --chip esp32c3 -p COM5 -b 460800 write_flash 0x0 build/merged-binary.bin
```

**方式三：标准 IDF 流程**

```powershell
idf.py -p COM5 flash monitor
```

分区布局：`0x0 bootloader` / `0x8000 分区表` / `0xd000 ota_data` / `0x10000 app` / `0x300000 assets`。

## 目录结构

```
main/application.*        主事件循环、协议生命周期
main/device_state_machine 状态机
main/boards/alin-c3/      本板：引脚、屏幕、表情、舵机、灯带、网页控制台
main/boards/common/       板级通用能力（WiFi、按键、电源等）
main/audio/               编解码、I2S、唤醒词
main/display/ main/led/   显示与灯驱动
main/protocols/           WebSocket 与 MQTT+UDP
main/mcp_server.*         设备端 MCP 工具
scripts/build.py          构建入口
partitions/               分区表
```

## 许可

MIT，见 [LICENSE](LICENSE)。原始项目版权归 [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) 及其贡献者。
