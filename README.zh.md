<p align="center">
  <img src="https://img.shields.io/badge/Claude_Code-Plugin-D97757?style=for-the-badge&labelColor=F0EEE6" alt="Claude Code 插件">
  <img src="https://img.shields.io/badge/version-0.1.2-C15F3C?style=for-the-badge&labelColor=F0EEE6" alt="版本 0.1.2">
  <img src="https://img.shields.io/badge/status-pre--release-B8860B?style=for-the-badge&labelColor=F0EEE6" alt="状态：预发布">
  <img src="https://img.shields.io/badge/license-MIT-788C5D?style=for-the-badge&labelColor=F0EEE6" alt="MIT 许可证">
</p>

<p align="center"><strong>第一次就能打印成功，坏了也能修的 FDM 零件设计。</strong></p>

<p align="center">
  <a href="#它做什么">它做什么</a> ·
  <a href="#六条硬性规则">硬性规则</a> ·
  <a href="#检查脚本">检查脚本</a> ·
  <a href="#安装">安装</a> ·
  <a href="#局限">局限</a> ·
  <a href="README.md">English</a>
</p>

---

`fdm-design` 是一个 Claude Code skill，用于设计、修改和审查 FDM/FFF 打印零件，重点是电子设备外壳、
支架和多件式外壳。它不绑定 CAD 软件（SolidWorks、Fusion、Onshape、FreeCAD、OpenSCAD、CadQuery、
build123d 都可以）。示例默认 Bambu Lab A1/X1、0.4 mm 喷嘴、PETG 或 PLA；规则本身以打印机、喷嘴和
材料为参数。

## 它做什么

- 一份简短的 [`SKILL.md`](skills/fdm-design/SKILL.md)（少于 200 行）：固定约定、六条硬性规则、
  十步流程和参考文件索引。
- 九份参考文件存放具体数字，每个数字都标注来源和置信度（一手、二手或未核实）：DfAM 规则、
  配合与热熔螺母、结构、连接器、线缆走线、外壳接缝、验证、来源，以及一个匿名案例。
- 四个 Python 检查脚本，助手或你自己都可以对导出的网格和 G-code 运行。

skill 强制的约定：角度一律**从竖直方向**量（切片器的支撑阈值是从水平方向量的，skill 会换算）；
间隙一律写**每边**；每个尺寸标注 measured / datasheet / reference / placeholder；每个结论标注
CAD-verified / sliced / printed。

## 六条硬性规则

每一条都来自一次真实改装中发生过的失败（[案例](skills/fdm-design/references/case-study.md)）。

| # | 失败 | 规则 |
|---|---|---|
| 1 | 关着支撑切片，得出"零支撑" | 声称免支撑，必须同时有：按声明阈值**开启**支撑的切片结果，和一次独立的几何悬垂审计；桥接逐个列出跨度 |
| 2 | 高打印柱加盲孔热熔螺母，一根断了整个壳报废 | 每条承力路径做失效后果分析；优先用可从外部更换的金属铜柱或贯穿螺栓；打印凸台只定位或承受轻载 |
| 3 | 连接器开孔按插座做布尔切割 | 按插头注塑外壳包络 + 每边间隙开孔，检查啮合深度，加导入倒角，留手指和卡扣操作空间；实测真实线缆 |
| 4 | 线长买不到，线缆压在模块上 | 先按现货线长和弯曲半径画走线通道；不从热源上方走；线缆两端都能够到 |
| 5 | 外壳分型无视参考设计的止口 | 照搬参考止口或舌槽；统一边缘处理；每个开孔只在一个零件内；左右面板对称 |
| 6 | 未经同意的结构改动（外壳加高 18 mm） | 外形尺寸、分型、接口位置和安装孔的改动都要先获明确同意；每处偏离都要报告 |

另有一条针对委派工作的规则：**检查必须有可能失败**；验收时要看实际产出（渲染图、剖面、开启支撑的
切片预览），而不是只看执行方的总结。

## 检查脚本

全部在 [`skills/fdm-design/scripts/`](skills/fdm-design/scripts/)。需要 Python 3.10+ 和 numpy；
trimesh 和 manifold3d 可选。退出码：0 通过，1 失败，2 无法判定或出错。

| 脚本 | 检查内容 |
|---|---|
| `overhang_audit.py` | 床面以外、超过悬垂限值的朝下面；水平天花板分为桥接（附估算跨度）、悬臂（台阶、沉头孔环）或悬空；文本或 JSON 输出 |
| `slice_support_check.py` | 强制开启支撑、按阈值调用 Bambu Studio / OrcaSlicer 切片，或解析你导出的 G-code / 3MF；支撑关闭或阈值不符时拒绝判定通过 |
| `mesh_check.py` | 水密、法向一致、法向朝外、连通体数量、成型尺寸 |
| `interference_check.py` | 两两求交体积（有 manifold3d 时精确计算，否则报告为无法判定），可列出有意的过盈配合 |

```bash
python skills/fdm-design/scripts/overhang_audit.py part.stl --max-overhang 45 --max-bridge 10
python skills/fdm-design/scripts/slice_support_check.py --gcode plate_1.gcode --max-overhang 45
python skills/fdm-design/scripts/mesh_check.py part.stl --printer a1
python skills/fdm-design/scripts/interference_check.py shell.stl board.stl plug.stl
```

测试集让每个检查都跑一遍必须失败的样例：悬臂台阶、59° 斜坡、没有牺牲层的沉头孔环、悬空孤岛、
关闭支撑的 G-code、相互重叠的方块、开口网格。

## 安装

### 作为插件安装

逐条输入以下斜杠命令：

```
/plugin marketplace add baizhiyuan/fdm-design-skill
```

```
/plugin install fdm-design@fdm-design-skill
```

### 手动复制 skill

```bash
git clone https://github.com/baizhiyuan/fdm-design-skill.git
mkdir -p ~/.claude/skills
cp -r fdm-design-skill/skills/fdm-design ~/.claude/skills/
python3 -m pip install numpy            # 可选：trimesh manifold3d
```

请求涉及 FDM 打印零件时，skill 会自动加载。查看安装情况：`ls ~/.claude/skills/fdm-design`，
或在 Claude Code 中运行 `/plugin`。

## 局限

- 不适用于树脂、CNC 或注塑。
- [`sources.md`](skills/fdm-design/references/sources.md) 中标为未核实的数字仍待确认：HDMI 插头
  外壳尺寸、SATA 弯曲半径、支撑和悬垂墙在 G-code 中的标签原文、M4 到 M6 两组相互冲突的热熔螺母
  数据、材料收缩率。
- 切片器命令行调用按厂商文档编写，未在 CI 中实际运行（CI 里没有切片器）；G-code 解析用合成文件测试。
- 悬垂审计用采样点估算桥接跨度，不预测下垂、翘边或冷却质量。请先打试件。

## 开发

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python scripts/validate.py
.venv/bin/python -m pytest -q tests
```

参见 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [AGENTS.md](AGENTS.md)。

## 许可与致谢

以 [MIT 许可证](LICENSE) 发布。

以下 MIT / MIT-0 项目提供了思路，在此致谢（未逐字复制文本或代码；细节见
[`sources.md`](skills/fdm-design/references/sources.md)）：

- [alexlenk/3d-printing](https://github.com/alexlenk/3d-printing)：每处偏离都需确认、每个检查都做负向测试、实打的连接器数据。
- [gjaloyan/print3d-designer](https://github.com/gjaloyan/print3d-designer)：切片器命令行的坑、按法向分级的悬垂检查、PETG 悬垂和桥接数据。
- [KD5RYN/b123d-print](https://github.com/KD5RYN/b123d-print)：规则编号、配合间隙表、桥接默认值、处理悬垂的优先顺序。
- [pthompson8594/openscad-skill](https://github.com/pthompson8594/openscad-skill)：植入缺陷的自测。
- [earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad)：按关注点拆分、把切片纳入流程。

Bambu Lab、Prusa Research、Stratasys、USB-IF、TIA、CNC Kitchen、Hubs 等来源的设计数据，在参考文件中逐个数字注明出处。

**声明。** 这是一个独立的社区项目，与 Anthropic、Bambu Lab 或文中提到的任何厂商均无关联，也未获其授权或认可。
