# LLMChess 训练 Pipeline 测试

本目录包含用于验证 LLM 训练 pipeline 的测试脚本和示例数据。

## 目录结构

```
LLMChess/
├── tests/
│   ├── __init__.py
│   └── test_pipeline.py    # 完整训练 pipeline 测试
├── data/
│   └── sample_train.json   # 示例训练数据
└── README.md               # 本文档
```

## 快速开始

### 运行测试

在 LLMChess 目录下执行：

```bash
python tests/test_pipeline.py
```

这将运行以下测试：

1. **模型前向传播测试** - 验证 GPT2 模型的 forward pass
2. **数据处理测试** - 验证文本清洗和 BPE 分词
3. **训练步骤测试** - 验证单个训练步骤（forward、backward、optimizer step）
4. **文本生成测试** - 验证贪婪解码生成
5. **完整 Pipeline 测试** - 验证多步训练循环

### 准备训练数据

使用示例数据或准备您自己的训练数据：

```bash
# 示例数据位于
data/sample_train.json

# 数据格式
[
  {"text": "您的训练文本1"},
  {"text": "您的训练文本2"}
]
```

### 开始训练

使用示例数据训练模型：

```python
from models.gpt2 import GPT2, GPTConfig
from data import TextDataset, BPETokenizer, collate_fn
from scripts import Trainer
from torch.utils.data import DataLoader

config = GPTConfig(
    vocab_size=10000,
    hidden_size=256,
    num_layers=4,
    num_heads=4
)

model = GPT2(config)
tokenizer = BPETokenizer()
dataset = TextDataset("data/sample_train.json", tokenizer)
dataloader = DataLoader(dataset, batch_size=2, collate_fn=collate_fn)

trainer = Trainer(model, dataloader)
trainer.train(num_epochs=10)
```

## 测试说明

测试脚本使用随机生成的数据进行快速验证，确保所有核心组件正常工作：

- 模型初始化和前向传播
- 损失计算和反向传播
- 优化器更新
- 文本生成解码

所有测试都可以在 CPU 上快速运行，不需要 GPU。

## 自定义测试

要测试自定义模型配置：

```python
config = GPTConfig(
    vocab_size=5000,      # 词汇表大小
    hidden_size=128,      # 隐藏层维度
    num_layers=2,        # Transformer 层数
    num_heads=4,         # 注意力头数
    max_seq_length=512    # 最大序列长度
)
model = GPT2(config)
```

## 依赖

测试脚本依赖以下模块：

- `torch` - PyTorch 深度学习框架
- `models.gpt2` - GPT2 模型实现
- `data` - 数据处理模块
- `scripts` - 训练脚本和工具

确保这些模块在您的 Python 环境中可用。
