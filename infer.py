from webapp.loader import *
from webapp.text_model import *
from bert import tokenization
import warnings

warnings.filterwarnings('ignore')
import time


def evaluate(sess, dev_data):
    '''
    批量的形式计算验证集或测试集上数据的平均loss，平均accuracy
    '''
    data_len = 0
    total_loss = 0.0
    total_acc = 0.0
    for batch_ids, batch_mask, batch_segment, batch_label \
            in batch_iter(dev_data, config.batch_size):
        batch_len = len(batch_ids)
        data_len += batch_len
        feed_dict = feed_data(batch_ids, batch_mask, batch_segment, batch_label, 1.0)
        loss, acc = sess.run([model.loss, model.acc], feed_dict=feed_dict)
        total_loss += loss * batch_len
        total_acc += acc * batch_len
    return total_loss / data_len, total_acc / data_len


def feed_data(batch_ids, batch_mask, batch_segment, batch_label, keep_prob):
    '''
    构建text_model需要传入的数据
    '''
    feed_dict = {
        model.input_ids: np.array(batch_ids),
        model.input_mask: np.array(batch_mask),
        model.segment_ids: np.array(batch_segment),
        model.labels: np.array(batch_label),
        model.keep_prob: keep_prob
    }
    return feed_dict


def getResult(user_input_text):
    config = TextConfig()
    model = TextCNN(config)
    save_dir = os.path.join(config.output_dir, "checkpoints/textcnn")
    save_path = os.path.join(save_dir, 'best_validation')
    label_list = label_static
    tokenizer = tokenization.FullTokenizer(vocab_file=config.vocab_file, do_lower_case=False)

    config.is_training = False
    session = tf.Session()
    session.run(tf.global_variables_initializer())
    saver = tf.train.Saver()
    saver.restore(sess=session, save_path=save_path)

    text = user_input_text

    try:
        start_time = time.time()
        texts = [text]
        # input texts
        examples = []
        set_type = 'test'
        for i, text in enumerate(texts):
            guid = "%s-%s" % (set_type, i)
            text_a = tokenization.convert_to_unicode(text)
            examples.append(
                InputExample(guid=guid, text_a=text_a, text_b=None, label=None))

        data = convert_examples_to_features(examples, label_list, config.seq_length, tokenizer)
        input_ids, input_mask, segment_ids = [], [], []
        for features in data:
            input_ids.append(features['input_ids'])
            input_mask.append(features['input_mask'])
            segment_ids.append(features['segment_ids'])

        # feed data
        feed_dict = {
            model.input_ids: np.array(input_ids),
            model.input_mask: np.array(input_mask),
            model.segment_ids: np.array(segment_ids),
            model.keep_prob: 1.0,
        }
        y_pred_cls = session.run(model.y_pred_cls, feed_dict=feed_dict)
        assert len(y_pred_cls) == 1
        result = label_list[y_pred_cls[0]]
        return result
    except Exception as e:
        return ('Error :{}'.format(e))


if __name__ == '__main__':

    print('Loading Model...')
    config = TextConfig()
    model = TextCNN(config)
    save_dir = os.path.join(config.output_dir, "checkpoints/textcnn")
    save_path = os.path.join(save_dir, 'best_validation')
    label_list = label_static
    tokenizer = tokenization.FullTokenizer(vocab_file=config.vocab_file, do_lower_case=False)

    config.is_training = False
    session = tf.Session()
    session.run(tf.global_variables_initializer())
    saver = tf.train.Saver()
    saver.restore(sess=session, save_path=save_path)

    while True:
        text = input("Please input texts for classification, input 'q' and Enter to quit. \n")
        if text == 'q':
            break
        print('Please wait...')
        try:
            start_time = time.time()
            texts = [text]
            # input texts
            examples = []
            set_type = 'test'
            for i, text in enumerate(texts):
                guid = "%s-%s" % (set_type, i)
                text_a = tokenization.convert_to_unicode(text)
                examples.append(
                    InputExample(guid=guid, text_a=text_a, text_b=None, label=None))

            data = convert_examples_to_features(examples, label_list, config.seq_length, tokenizer, cmd_infer=True)
            input_ids, input_mask, segment_ids = [], [], []
            for features in data:
                input_ids.append(features['input_ids'])
                input_mask.append(features['input_mask'])
                segment_ids.append(features['segment_ids'])

            # feed data
            feed_dict = {
                model.input_ids: np.array(input_ids),
                model.input_mask: np.array(input_mask),
                model.segment_ids: np.array(segment_ids),
                model.keep_prob: 1.0,
            }
            y_pred_cls = session.run(model.y_pred_cls, feed_dict=feed_dict)
            assert len(y_pred_cls) == 1
            print('Result: ' + label_list[y_pred_cls[0]], ', cost {:.3}s'.format(
                time.time() - start_time))
        except Exception as e:
            print('Error :{}'.format(e))
