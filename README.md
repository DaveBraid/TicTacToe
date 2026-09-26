# 表格型 Q-learning 玩井字棋

本仓库整理了[埠默笙声声声脉](https://www.cnblogs.com/wsy950409/)的井字棋强化学习系列：原作者的 Pygame 游戏源码、预训练 Q 表、字体与贴图，以及六篇博客正文和 31 张图片的离线备份。按顺序阅读请从 [handbooks/](handbooks/README.md) 开始。

## 仓库内容

- `TicTacToe Game.py`：原作者的人机、机机对战程序，支持查看 Q 值。
- `Q_table_dict.pkl`：原作者提供的预训练 Q 表；启动游戏时直接读取。
- `texture/`：游戏使用的图片和字体。
- `handbooks/`：高中生适用的 Q-table 概念入门、六篇编号文章的阅读提要与离线备份、图片和来源校验清单。
- `scripts/backup_articles.py`：重新下载文章及图片的脚本，联网时运行。

源码与素材取自原作者 [Gitee 项目](https://gitee.com/wsy950409/q-table-play-tic-tac-toe)的提交 `41f6f0e05687014267fb96bfd9a5849deb84a373`，保留其 [木兰宽松许可证第 2 版](LICENSE)及[原 README 备份](handbooks/99-原项目说明.md)。游戏源码按原样保存；博客中的环境和训练代码没有另行拼接成运行脚本。

## 部署与运行

三个系统均推荐先安装 Anaconda 或 Miniconda，再用 Conda 创建独立的 Python 3.11 环境。游戏需要图形桌面，并须从仓库根目录启动，以便读取 Q 表和 `texture/` 素材。

macOS / Linux（终端）：

```bash
conda create -n tictactoe python=3.11 -y
conda activate tictactoe
python -m pip install -r requirements.txt
python "TicTacToe Game.py"
```

Windows（Anaconda Prompt 或已启用 Conda 的 PowerShell）：

```powershell
conda create -n tictactoe python=3.11 -y
conda activate tictactoe
python -m pip install -r requirements.txt
python ".\TicTacToe Game.py"
```

首次使用 Conda 时，若 `conda activate` 不可用，先运行 `conda init` 并重新打开终端。启动后在界面选择双方策略（Q、random 或 human），点击 START 对战；CHEAT 可显示蓝方当前局面的 Q 值。

## 离线阅读

直接用浏览器打开 [handbooks/01-原文备份.html](handbooks/01-原文备份.html)，其余五篇可从 [学习路线](handbooks/README.md) 进入。正文图片均指向仓库内的 `handbooks/assets/`；`manifest.json` 记录原始网址和 SHA-256。首次备份后不需要联网阅读或启动游戏。

## 鸣谢

感谢原作者[埠默笙声声声脉](https://www.cnblogs.com/wsy950409/)分享[强化学习实战系列文章](https://www.cnblogs.com/wsy950409/p/15645049.html)与[Q table play TicTacToe 原项目](https://gitee.com/wsy950409/q-table-play-tic-tac-toe)。
