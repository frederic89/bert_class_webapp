# Django框架下的Bert文本分类平台

——基于bert的中文新闻分类平台，详见参考2

![文本分类平台](https://i.imgur.com/v7J89SQ.gif)

### 更新日志

2022.06.26 修改代码，加强逻辑可读性；在命令行日志中显示文本在各分类的判断概率

2022.06.09 本地化Bootstrap、jQuery的静态文件(JS和CSS)，方便部署uwsgi等本地化部署

2022.06.04 增加模型标签名配置或语料库中分类标签名是否一致检查

2022.05.22 将标签配置统一放于text_model.py中

### 安装依赖

Python版本：Python 3.6.13  +  Tensorflow 1.9.0（此为CPU版本，GPU版本tensorflow-gpu请自行调试）

从pip安装依赖环境，建议先使用pyenv等新建python虚拟环境：

```python
pip3 install -r requirements.txt # 安装依赖包
```

（注：如碰到具体版本有问题，请手动安装合适版本）

### 分类系统运行

请先训练模型，见“**数据的训练**”。

1. 网页运行：

   python3 manage.py runserver 8000

   打开http://127.0.0.1:8000 访问

2. 另外提供命令行交互方式：

   python3 infer.py

### 数据的训练

1. BERT模型的下载地址：[BERT-Base, Chinese](https://storage.googleapis.com/bert_models/2018_11_03/chinese_L-12_H-768_A-12.zip) : Chinese Simplified and Traditional, 12-layer, 768-hidden, 12-heads, 110M parameters。**注意**：请下载后请置于根目录下的bert_model文件夹中，等待预备训练。（正确的语料路径应为/bert_model/chinese_L-12_H-768_A-12）

2. 数据集是新闻数据集，涉及10个类别（体育、财经、房产、家居、教育、科技、时尚、时政、游戏、娱乐），下载链接：[https://pan.baidu.com/s/11AuC5g47rnsancf6nfKdiQ](https://pan.baidu.com/s/11AuC5g47rnsancf6nfKdiQ) 密码:1vdg。**注意**：请下载后请置于项目根目录下的corpus/cnews文件夹中（如没有路径，请照此新建）。

3. 训练分类模型：
```python
python3 text_run.py train
```
​	or   带重定向导出日志运行:  
```python
python3 text_run.py train 2> train.txt
```
4. 用测试集评价模型：

```python
python3 text_run.py test 
```

### Todo

​	后期考虑针对小样本(few shot)语料训练进行优化

### 参考

1. 源码中框架TextCNN(TEXT_BERT_CNN)来自[https://github.com/cjymz886/text_bert_cnn](https://github.com/cjymz886/text_bert_cnn) 的项目。

2. https://blog.csdn.net/weixin_43486940/article/details/124188746