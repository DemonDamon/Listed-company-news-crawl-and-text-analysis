import __init__

from Kite import config
from Kite import utils
from Leorio.tokenization import Tokenization

from gensim import corpora
from gensim import models

import logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s",
                    datefmt="%a, %d %b %Y %H:%M:%S")


class TopicModelling(object):

    def __init__(self):
        self.tokenization = Tokenization(import_module="jieba",
                                         user_dict=config.USER_DEFINED_DICT_PATH,
                                         chn_stop_words_dir=config.CHN_STOP_WORDS_PATH)

    def create_dictionary(self, raw_documents_list, savepath=None):
        """
        将文中每个词汇关联唯一的ID，因此需要定义词汇表
        :param: raw_documents_list, 原始语料列表，每个元素即文本，如["洗尽铅华...", "风雨赶路人...", ...]
        :param: savepath, corpora.Dictionary对象保存路径
        """
        documents_token_list = []
        for doc in raw_documents_list:
            documents_token_list.append(self.tokenization.cut_words(doc))
        _dict = corpora.Dictionary(documents_token_list)
        if savepath:
            _dict.save(savepath)
        return _dict, documents_token_list

    def create_bag_of_word_representation(self, raw_documents_list, dict_save_path=None, bow_vector_save_path=None):
        corpora_dictionary, documents_token_list = self.create_dictionary(raw_documents_list, savepath=dict_save_path)
        bow_vector = [corpora_dictionary.doc2bow(doc_token) for doc_token in documents_token_list]
        if bow_vector_save_path:
            corpora.MmCorpus.serialize(bow_vector_save_path, bow_vector)
        return documents_token_list, corpora_dictionary, bow_vector

    def transform_vectorized_corpus(self, corpora_dictionary, bow_vector, model_type="lda", model_save_path=None):
        if model_type == "lsi":
            tfidf_vector = models.TfidfModel(bow_vector)[bow_vector]
            model = models.LsiModel(tfidf_vector,
                                    id2word=corpora_dictionary,
                                    num_topics=config.TOPIC_NUMBER)  # 初始化模型
            model_vector = model[tfidf_vector]
            if model_save_path:
                model.save(model_save_path)
            return tfidf_vector, model_vector
        elif model_type == "lda":
            tfidf_vector = models.TfidfModel(bow_vector)[bow_vector]
            model = models.LdaModel(tfidf_vector,
                                    id2word=corpora_dictionary,
                                    num_topics=config.TOPIC_NUMBER)  # 初始化模型
            model_vector = model[tfidf_vector]
            if model_save_path:
                model.save(model_save_path)
            return tfidf_vector, model_vector
        elif model_type == "tfidf":
            model = models.TfidfModel(bow_vector)  # 初始化
            tfidf_vector = model[bow_vector]  # 将整个语料进行转换
            if model_save_path:
                model.save(model_save_path)
            return tfidf_vector

    def load_transform_model(self, model_path):
        if ".tfidf" in model_path:
            return models.TfidfModel.load(model_path)
        elif ".lsi" in model_path:
            return models.LsiModel.load(model_path)
        elif ".lda" in model_path:
            return models.LdaModel.load(model_path)


if __name__ == "__main__":
    from Hisoka.classifier import Classifier
    from Kite.database import Database
    from sklearn import preprocessing

    database = Database()
    topicmodelling = TopicModelling()
    raw_documents_list = []
    Y = []
    for row in database.get_collection("stocknews", "sz000001").find():
        if "3DaysLabel" in row.keys():
            raw_documents_list.append(row["Article"])
            if row["3DaysLabel"] == "中性":
                Y.append(0)
            elif row["3DaysLabel"] == "利好":
                Y.append(1)
            elif row["3DaysLabel"] == "利空":
                Y.append(2)
    le = preprocessing.LabelEncoder()

    _, corpora_dictionary, bow_vector = topicmodelling.create_bag_of_word_representation(raw_documents_list)
    # for _vector in bow_vector:
    _, model_vector = topicmodelling.transform_vectorized_corpus(corpora_dictionary,
                                                                 bow_vector,
                                                                 model_type="lda")
    csr_matrix = utils.convert_to_csr_matrix(model_vector)
    train_x, train_y, test_x, test_y = utils.generate_training_set(csr_matrix, Y)
    classifier = Classifier()
    classifier.svm(train_x, train_y, test_x, test_y)