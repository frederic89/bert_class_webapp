# coding:utf-8
import time
import sys
from sklearn import metrics
# from webapp.text_model import *
from webapp.loader import *


def evaluate(sess, dev_data):
    """批量的形式计算验证集或测试集上数据的平均loss，平均accuracy"""
    data_len = 0
    total_loss = 0.0
    total_acc = 0.0
    for batch_ids, batch_mask, batch_segment, batch_label in batch_iter(dev_data, config.batch_size):
        batch_len = len(batch_ids)
        data_len += batch_len
        feed_dict = feed_data(batch_ids, batch_mask, batch_segment, batch_label, 1.0)
        loss, acc = sess.run([model.loss, model.acc], feed_dict=feed_dict)
        total_loss += loss * batch_len
        total_acc += acc * batch_len
    return total_loss / data_len, total_acc / data_len


def feed_data(batch_ids, batch_mask, batch_segment, batch_label, keep_prob):
    """构建text_model需要传入的数据"""
    feed_dict = {
        model.input_ids: np.array(batch_ids),
        model.input_mask: np.array(batch_mask),
        model.segment_ids: np.array(batch_segment),
        model.labels: np.array(batch_label),
        model.keep_prob: keep_prob
    }
    return feed_dict


def optimistic_restore(session, save_file):
    """载入bert模型"""
    reader = tf.train.NewCheckpointReader(save_file)
    saved_shapes = reader.get_variable_to_shape_map()
    var_names = sorted([(var.name, var.name.split(':')[0]) for
                        var in tf.global_variables()
                        if var.name.split(':')[0] in saved_shapes])
    restore_vars = []
    name2var = dict(zip(map(lambda x: x.name.split(':')[0], tf.global_variables()), tf.global_variables()))
    with tf.variable_scope('', reuse=True):
        for var_name, saved_var_name in var_names:
            curr_var = name2var[saved_var_name]
            var_shape = curr_var.get_shape().as_list()
            if var_shape == saved_shapes[saved_var_name]:
                # print("going to restore.var_name:",var_name,";saved_var_name:",saved_var_name)
                restore_vars.append(curr_var)
            else:
                print("variable not trained.var_name:", var_name)
    saver = tf.train.Saver(restore_vars)
    saver.restore(session, save_file)


def train():
    """训练模型text_bert_cnn模型"""

    tensorboard_dir = os.path.join(config.output_dir, "tensorboard/textcnn")
    save_dir = os.path.join(config.output_dir, "checkpoints/textcnn")
    if not os.path.exists(tensorboard_dir):
        os.makedirs(tensorboard_dir)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    save_path = os.path.join(save_dir, 'best_validation')

    start_time = time.time()

    tf.logging.info("*****************Loading training data*****************")
    train_examples = TextProcessor().get_train_examples(config.data_dir)
    trian_data = convert_examples_to_features(train_examples, label_list, config.seq_length, tokenizer)

    tf.logging.info("*****************Loading dev data*****************")
    dev_examples = TextProcessor().get_dev_examples(config.data_dir)
    dev_data = convert_examples_to_features(dev_examples, label_list, config.seq_length, tokenizer)

    tf.logging.info("Time cost: %.3f seconds...\n" % (time.time() - start_time))

    tf.logging.info("Building session and restore bert_model...\n")
    session = tf.Session()
    saver = tf.train.Saver()
    session.run(tf.global_variables_initializer())

    tf.summary.scalar("loss", model.loss)
    tf.summary.scalar("accuracy", model.acc)
    merged_summary = tf.summary.merge_all()
    writer = tf.summary.FileWriter(tensorboard_dir)
    writer.add_graph(session.graph)
    optimistic_restore(session, config.init_checkpoint)

    tf.logging.info('Training and evaluating...\n')
    best_acc = 0
    last_improved = 0  # record global_step at best_val_accuracy
    flag = False

    print("将动态展示每个批次的输入标签序号")

    for epoch in range(config.num_epochs):
        batch_train = batch_iter(trian_data, config.batch_size)
        start = time.time()
        tf.logging.info('Epoch:%d' % (epoch + 1))
        for batch_ids, batch_mask, batch_segment, batch_label in batch_train:
            print(batch_label)  # 打印每个批次的输入标签序号
            feed_dict = feed_data(batch_ids, batch_mask, batch_segment, batch_label, config.keep_prob)
            _, global_step, train_summaries, train_loss, train_accuracy = session.run([model.optim, model.global_step,
                                                                                       merged_summary, model.loss,
                                                                                       model.acc], feed_dict=feed_dict)
            if global_step % config.print_per_batch == 0:
                end = time.time()
                val_loss, val_accuracy = evaluate(session, dev_data)
                merged_acc = (train_accuracy + val_accuracy) / 2
                if merged_acc > best_acc:
                    saver.save(session, save_path)
                    best_acc = merged_acc
                    last_improved = global_step
                    improved_str = '*'
                else:
                    improved_str = ''
                tf.logging.info(
                    "step: {},train loss: {:.3f}, train accuracy: {:.3f}, val loss: {:.3f}, val accuracy: {:.3f},training speed: {:.3f}sec/batch {}".format(
                        global_step, train_loss, train_accuracy, val_loss, val_accuracy,
                        (end - start) / config.print_per_batch, improved_str))
                start = time.time()

            if global_step - last_improved > config.require_improvement:
                tf.logging.info("No optimization over 1500 steps, stop training") # TODO 1500
                flag = True
                break
        if flag:
            break
        config.lr *= config.lr_decay


def test():
    """testing"""

    save_dir = os.path.join(config.output_dir, "checkpoints/textcnn")
    save_path = os.path.join(save_dir, 'best_validation')

    if not os.path.exists(save_dir):
        tf.logging.info("maybe you don't train")
        exit()

    tf.logging.info("*****************Loading testing data*****************")
    test_examples = TextProcessor().get_test_examples(config.data_dir)
    test_data = convert_examples_to_features(test_examples, label_list, config.seq_length, tokenizer)
    input_ids, input_mask, segment_ids = [], [], []
    for features in test_data:
        input_ids.append(features['input_ids'])
        input_mask.append(features['input_mask'])
        segment_ids.append(features['segment_ids'])

    config.is_training = False
    session = tf.Session()
    session.run(tf.global_variables_initializer())
    saver = tf.train.Saver()
    saver.restore(sess=session, save_path=save_path)

    tf.logging.info('Testing...')
    test_loss, test_accuracy = evaluate(session, test_data)
    msg = 'Test Loss: {0:>6.2}, Test Acc: {1:>7.2%}'
    tf.logging.info(msg.format(test_loss, test_accuracy))

    batch_size = config.batch_size
    data_len = len(test_data)
    num_batch = int((data_len - 1) / batch_size) + 1
    y_test_cls = [features['label_ids'] for features in test_data]
    y_pred_cls = np.zeros(shape=data_len, dtype=np.int32)

    for i in range(num_batch):
        start_id = i * batch_size
        end_id = min((i + 1) * batch_size, data_len)
        feed_dict = {
            model.input_ids: np.array(input_ids[start_id:end_id]),
            model.input_mask: np.array(input_mask[start_id:end_id]),
            model.segment_ids: np.array(segment_ids[start_id:end_id]),
            model.keep_prob: 1.0,
        }
        y_pred_cls[start_id:end_id] = session.run(model.y_pred_cls, feed_dict=feed_dict)

    '''
    输出测试矩阵
    '''
    # evaluate
    tf.logging.info("Precision, Recall and F1-Score...")
    tf.logging.info(metrics.classification_report(y_test_cls, y_pred_cls, target_names=label_list))

    tf.logging.info("Confusion Matrix...")
    cm = metrics.confusion_matrix(y_test_cls, y_pred_cls)
    tf.logging.info(cm)


def get_single_pre(final_model, label_list, tokenizer, session):
    """
    结果预测
    """
    config = TextConfig()
    save_dir = os.path.join(config.output_dir, "checkpoints/textcnn")
    save_path = os.path.join(save_dir, 'best_validation')

    if not os.path.exists(save_dir):
        tf.logging.info("训练路径模型不存在，请检查：‘result/checkpoints/textcnn/’，"
                        "路径下是否有保存模型：best_validation.data-00000-of-00001")
        exit()

    tf.logging.info("*****************读取预测文件*****************")
    test_example = TextProcessor().get_single_pre_example(config.data_dir)
    """single_test_data返回的是数组，里面的每个单元是字典"""
    single_test_data = convert_examples_to_features(test_example, label_list, config.seq_length, tokenizer)

    input_id, input_mask, segment_id = [], [], []

    """重塑convert_examples_to_features的features结构，具体结构请见该函数"""
    for features in single_test_data:
        input_id.append(features['input_ids'])
        input_mask.append(features['input_mask'])
        segment_id.append(features['segment_ids'])

    # config.is_training = False
    # session = tf.Session()
    # session.run(tf.global_variables_initializer())
    # saver = tf.train.Saver()
    # saver.restore(sess=session, save_path=save_path)

    print('开始预测...')
    # test_loss, test_accuracy = evaluate(session, test_data)
    # msg = 'Test Loss: {0:>6.2}, Test Acc: {1:>7.2%}'
    # tf.logging.info(msg.format(test_loss, test_accuracy))

    # batch_size = config.batch_size
    # data_len = len(single_test_data)
    # num_batch = int((data_len - 1) / batch_size) + 1
    y_test_cls = [features['label_ids'] for features in single_test_data]
    y_pred_cls = np.zeros(shape=1, dtype=np.int32)

    feed_dict = {
        final_model.input_ids: np.array(input_id),
        final_model.input_mask: np.array(input_mask),
        final_model.segment_ids: np.array(segment_id),
        final_model.keep_prob: 1.0,
    }
    "final_model.y_pred_cls在text_model的self.y_pred_cls = tf.argmax(tf.nn.softmax(self.logits), 1)"
    y_pred_cls_dict = session.run({'y_pred_class_array': final_model.y_pred_cls, 'y_pred_prob_array': final_model.prob},
                                  feed_dict=feed_dict)
    pre_label = y_pred_cls_dict['y_pred_class_array'][0]
    print("预测index结果为：", pre_label)
    # y_pred_cls_dict['y_pred_prob_array'] is like: array([[......]])
    _prob = y_pred_cls_dict['y_pred_prob_array'].tolist()[0]  # numpy数组转换为列表，[0]再脱去嵌套的列表外壳
    return pre_label, _prob


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['train', 'test']:
        raise ValueError("""usage: python run_cnn.py [train / test]""")

    start_time = time.time()
    tf.logging.set_verbosity(tf.logging.INFO)
    config = TextConfig()
    label_list = TextProcessor().get_labels()
    print("预测文本分类的label_list：", label_list)
    tokenizer = tokenization.FullTokenizer(vocab_file=config.vocab_file, do_lower_case=False)
    # 初始化模型
    model = TextCNN(config)
    end_time = time.time()
    print("模型初始化时间：", end_time - start_time)

    if sys.argv[1] == 'train':
        train()
    elif sys.argv[1] == 'test':
        test()
    else:
        exit()
    #
    # print("label_list：", label_list)
    # # 模型预测
    # l_index = get_pre(model)
    # l_name = label_list[l_index]
    # end_time2 = time.time()
    # print("预测时间：", end_time2 - end_time)
    # print("预测结果为：", l_name)
