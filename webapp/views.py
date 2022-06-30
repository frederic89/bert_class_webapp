# coding:utf-8
from django.shortcuts import render
import time
import csv

# sys.path.append("..")
from webapp.text_model import *
from webapp.loader import *
import text_run as tr


def write_to_pre_test_tsv(data):
    """
    待预测信息写入
    """
    with open(r'corpus/cnews/pre_test.tsv', 'w', newline='', encoding='utf-8') as f:
        tsv_w = csv.writer(f, delimiter='\t')
        tsv_w.writerow([label_static[0], data])


def get_model():
    """
    模型初始化
    """
    g_config = TextConfig()
    save_dir = os.path.join(g_config.output_dir, "checkpoints/textcnn")
    save_path = os.path.join(save_dir, 'best_validation')

    g_start_time = time.time()
    tf.logging.set_verbosity(tf.logging.INFO)

    g_label_list = TextProcessor().get_labels()
    g_tokenizer = tokenization.FullTokenizer(vocab_file=g_config.vocab_file, do_lower_case=False)
    # 初始化模型
    g_model = TextCNN(g_config)
    g_end_time = time.time()
    g_config.is_training = False
    session = tf.Session()
    session.run(tf.global_variables_initializer())
    saver = tf.train.Saver()
    saver.restore(sess=session, save_path=save_path)
    print("模型初始化时间：", g_end_time - g_start_time)
    return g_model, g_label_list, g_tokenizer, session


# 模型获取
my_model, label_list, g_token, g_session = get_model()


def start(request):
    return render(request, 'start.html', {})


def get_ans(request):
    text = request.POST["input_text"]
    print("获取的文本：", text)
    if text is "":
        context = {
            "state": "1",
            "text": "输入的内容为空！请重新输入想要分类的文本！"
        }
        return render(request, 'error.html', context)
    else:
        if is_chinese_char(text):
            # 获取返回结果
            context = class_get(text)
            return render(request, 'user_class.html', context)

        else:
            context = {
                "state": "2",
                "text": "您输入的信息全为数字或英文，无法进行分类检测，请重新输入中文文本！"
            }
            return render(request, 'error.html', context)


# 输入检测
def is_chinese_char(s):
    """ 判断是否包含有中文汉字 """
    is_char = True
    for i in s:
        if u'\u4e00' <= i <= u'\u9fff':
            is_char = is_char | True
        else:
            is_char = is_char | False
    return is_char


def class_get(in_text):
    # 写入文本
    write_to_pre_test_tsv(in_text)
    start_time = time.time()
    # 模型预测, 返回概率
    index, pre_class_prob = tr.get_single_pre(my_model, label_list, g_token, g_session)
    print("各分类预测的概率为：", pre_class_prob)
    name = label_list[index]
    one_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    one_list[index] = 1
    end_time = time.time()
    pre_time = int((end_time - start_time)*1000)
    print("预测时间：", pre_time)
    print("预测结果为：", name)
    r_data = {
        "my_text": in_text,
        "pre_time": pre_time,
        "tiyu": one_list[0],
        "caijing": one_list[1],
        "fangchan": one_list[2],
        "jiaju": one_list[3],
        "jiaoyu": one_list[4],
        "keji": one_list[5],
        "shishang": one_list[6],
        "shizheng": one_list[7],
        "youxi": one_list[8],
        "yule": one_list[9]
    }
    return r_data
