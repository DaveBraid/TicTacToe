#!/bin/bash

# 定义颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取系统类型和架构
OS_TYPE=$(uname -s)
ARCH_TYPE=$(uname -m)

# 打印信息函数
info() {
    echo -e "${GREEN}[INFO] $1${NC}"
}
warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}
error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# 1. 安装 Miniconda 函数
install_miniconda() {
    info "正在检测系统环境..."

    local INSTALLER_NAME=""
    local DOWNLOAD_URL=""

    # 确定下载链接 (为了速度，使用清华源下载安装包)
    if [[ "$OS_TYPE" == "Linux" ]]; then
        if [[ "$ARCH_TYPE" == "x86_64" ]]; then
            INSTALLER_NAME="Miniconda3-latest-Linux-x86_64.sh"
        elif [[ "$ARCH_TYPE" == "aarch64" ]]; then
            INSTALLER_NAME="Miniconda3-latest-Linux-aarch64.sh"
        else
            error "不支持的架构: $ARCH_TYPE"
            return
        fi
    elif [[ "$OS_TYPE" == "Darwin" ]]; then
        if [[ "$ARCH_TYPE" == "x86_64" ]]; then
            INSTALLER_NAME="Miniconda3-latest-MacOSX-x86_64.sh"
        elif [[ "$ARCH_TYPE" == "arm64" ]]; then
            INSTALLER_NAME="Miniconda3-latest-MacOSX-arm64.sh"
        else
            error "不支持的架构: $ARCH_TYPE"
            return
        fi
    else
        error "不支持的系统: $OS_TYPE"
        return
    fi

    DOWNLOAD_URL="https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/$INSTALLER_NAME"

    info "系统检测: $OS_TYPE $ARCH_TYPE"
    info "准备下载: $INSTALLER_NAME"

    # 下载失败立即退出，避免执行错误页或不完整的安装包
    if command -v wget &> /dev/null; then
        wget -c "$DOWNLOAD_URL" -O "$INSTALLER_NAME" || {
            error "下载安装包失败。"
            return 1
        }
    elif command -v curl &> /dev/null; then
        curl -fL "$DOWNLOAD_URL" -o "$INSTALLER_NAME" || {
            error "下载安装包失败。"
            return 1
        }
    else
        error "未找到 wget 或 curl，无法下载。"
        return 1
    fi

    # 安装
    if [[ -f "$INSTALLER_NAME" ]]; then
        info "下载完成，开始安装..."
        bash "$INSTALLER_NAME"

        # 删除安装包
        rm -f "$INSTALLER_NAME"
        info "Miniconda 安装脚本执行完毕。请先退出本脚本并重新打开终端，确认 conda --version 可用后再配置镜像源。"
    else
        error "下载失败。"
    fi
}

# 2. 配置 Conda 源函数
config_conda_mirror() {
    echo -e "${BLUE}请选择 Conda 源:${NC}"
    echo "1. 清华大学源 (Tsinghua)"
    echo "2. 中科大源 (USTC)"
    echo "3. 恢复官方默认源 (Defaults)"
    read -p "请输入选项 [1-3]: " choice

    # Conda 会合并安装目录和用户目录中的配置；安装目录残留 defaults 会触发 Anaconda ToS
    if [[ "$choice" == "1" || "$choice" == "2" ]] && command -v conda &> /dev/null; then
        CONDA_ROOT_CONDARC="$(conda info --base 2>/dev/null)/.condarc"
        if [[ -f "$CONDA_ROOT_CONDARC" && "$CONDA_ROOT_CONDARC" != "$HOME/.condarc" ]]; then
            cp "$CONDA_ROOT_CONDARC" "$CONDA_ROOT_CONDARC.bak"
            rm -f "$CONDA_ROOT_CONDARC"
            warn "已停用安装目录中的旧配置，并备份至 $CONDA_ROOT_CONDARC.bak"
        fi
    fi

    # 备份现有配置
    if [[ -f ~/.condarc ]]; then
        cp ~/.condarc ~/.condarc.bak
        warn "已备份原配置至 ~/.condarc.bak"
    fi

    case $choice in
        1)
            info "正在切换至清华源..."
            cat > ~/.condarc << EOF
channels:
  - defaults
show_channel_urls: true
default_channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/msys2
custom_channels:
  conda-forge: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  msys2: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  bioconda: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  menpo: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  pytorch: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  pytorch-lts: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  simpleitk: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
EOF
            info "Conda 清华源配置完成。"
            ;;
        2)
            info "正在切换至中科大源..."
            cat > ~/.condarc << EOF
channels:
  - conda-forge
  - nodefaults
custom_channels:
  conda-forge: https://mirrors.ustc.edu.cn/anaconda/cloud
  bioconda: https://mirrors.ustc.edu.cn/anaconda/cloud
show_channel_urls: true
channel_priority: strict
EOF
            # 清除旧索引，避免继续命中过期频道缓存
            if command -v conda &> /dev/null; then
                conda clean -i -y
                if conda config --show channels | grep -Eq 'defaults|repo\.anaconda\.com'; then
                    warn "仍检测到 Anaconda 官方频道，请运行 conda config --show-sources 排查其他配置文件。"
                fi
            fi
            info "Conda 中科大源配置完成。"
            ;;
        3)
            info "正在恢复默认源..."
            rm -f ~/.condarc
            info "已删除 .condarc 配置文件，恢复为默认。"
            ;;
        *)
            error "无效选项。"
            ;;
    esac
}

# 3. 配置 Pip 源函数
config_pip_mirror() {
    echo -e "${BLUE}请选择 Pip 源:${NC}"
    echo "1. 清华大学源 (Tsinghua)"
    echo "2. 中科大源 (USTC)"
    echo "3. 恢复官方默认源 (PyPI)"
    read -p "请输入选项 [1-3]: " choice

    # 确保 .pip 目录存在
    mkdir -p ~/.pip

    case $choice in
        1)
            info "正在切换 Pip 至清华源..."
            # 兼容没有 pip 命令的情况，直接写文件
            cat > ~/.pip/pip.conf << EOF
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF
            info "Pip 清华源配置完成。"
            ;;
        2)
            info "正在切换 Pip 至中科大源..."
            cat > ~/.pip/pip.conf << EOF
[global]
index-url = https://mirrors.ustc.edu.cn/pypi/simple
[install]
trusted-host = mirrors.ustc.edu.cn
EOF
            info "Pip 中科大源配置完成。"
            ;;
        3)
            info "正在恢复 Pip 默认源..."
            rm -f ~/.pip/pip.conf
            info "已删除 pip.conf，恢复为官方默认。"
            ;;
        *)
            error "无效选项。"
            ;;
    esac
}

# 主菜单
main_menu() {
    while true; do
        echo -e "\n========================================"
        echo -e "      Python 环境配置助手 (Linux/Mac)   "
        echo -e "========================================"
        echo "1. 安装最新版 Miniconda"
        echo "2. 配置 Conda 镜像源 (换源)"
        echo "3. 配置 Pip 镜像源 (换源)"
        echo "4. 退出脚本"
        echo -e "========================================"
        read -p "请输入您的选择 [1-4]: " main_choice

        case $main_choice in
            1)
                install_miniconda
                ;;
            2)
                config_conda_mirror
                ;;
            3)
                config_pip_mirror
                ;;
            4)
                echo "退出。"
                exit 0
                ;;
            *)
                error "无效输入，请重新选择。"
                ;;
        esac
    done
}

# 运行主菜单
main_menu
