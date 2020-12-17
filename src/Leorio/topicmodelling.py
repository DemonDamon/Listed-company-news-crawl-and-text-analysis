import __init__
import os

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

    def create_dictionary(self, raw_documents_list, save_path=None):
        """
        将文中每个词汇关联唯一的ID，因此需要定义词汇表
        :param: raw_documents_list, 原始语料列表，每个元素即文本，如["洗尽铅华...", "风雨赶路人...", ...]
        :param: savepath, corpora.Dictionary对象保存路径
        """
        documents_token_list = []
        for doc in raw_documents_list:
            documents_token_list.append(self.tokenization.cut_words(doc))
        _dict = corpora.Dictionary(documents_token_list)
        # 找到只出现一次的token
        once_items = [_dict[tokenid] for tokenid, docfreq in _dict.dfs.items() if docfreq == 1]
        # 在documents_token_list的每一条语料中，删除只出现一次的token
        for _id, token_list in enumerate(documents_token_list):
            documents_token_list[_id] = list(filter(lambda token: token not in once_items, token_list))
        # 极端情况，某一篇语料所有token只出现一次，这样该篇新闻语料的token列表就变为空，因此删除掉
        documents_token_list = [token_list for token_list in documents_token_list if (len(token_list) != 0)]
        # 找到只出现一次的token对应的id
        once_ids = [tokenid for tokenid, docfreq in _dict.dfs.items() if docfreq == 1]
        # 删除仅出现一次的词
        _dict.filter_tokens(once_ids)
        # 消除id序列在删除词后产生的不连续的缺口
        _dict.compactify()
        if save_path:
            _dict.save(save_path)
        return _dict, documents_token_list

    def renew_dictionary(self, old_dict_path, new_raw_documents_list, new_dict_path=None):
        documents_token_list = []
        for doc in new_raw_documents_list:
            documents_token_list.append(self.tokenization.cut_words(doc))
        _dict = corpora.Dictionary.load(old_dict_path)
        _dict.add_documents(documents_token_list)
        if new_dict_path:
            old_dict_path = new_dict_path
        _dict.save(old_dict_path)
        logging.info("updated dictionary by another raw documents, and serialized in {} ... ".format(old_dict_path))
        return _dict, documents_token_list

    def create_bag_of_word_representation(self,
                                          raw_documents_list,
                                          old_dict_path=None,
                                          new_dict_path=None,
                                          bow_vector_save_path=None):
        if old_dict_path:
            # 如果存在旧的语料词典，就在原先词典的基础上更新，增加未有的词
            corpora_dictionary, documents_token_list = self.renew_dictionary(old_dict_path,
                                                                             raw_documents_list,
                                                                             new_dict_path=new_dict_path)
        else:
            # 否则重新创建词典
            corpora_dictionary, documents_token_list = self.create_dictionary(raw_documents_list,
                                                                              save_path=new_dict_path)
        # 根据新词典对文档(或语料)生成对应的词袋向量
        bow_vector = [corpora_dictionary.doc2bow(doc_token) for doc_token in documents_token_list]
        if bow_vector_save_path:
            corpora.MmCorpus.serialize(bow_vector_save_path, bow_vector)
        return documents_token_list, corpora_dictionary, bow_vector

    def transform_vectorized_corpus(self, corpora_dictionary, bow_vector, model_type="lda", model_save_path=None):
        # 如何没有保存任何模型，重新训练的情况下，可以选择该函数
        model_vector = None
        if model_type == "lsi":
            # LSI(Latent Semantic Indexing)模型，将文本从词袋向量或者词频向量(更好)，转为一个低维度的latent空间
            # 对于现实语料，目标维度在200-500被认为是"黄金标准"
            tfidf_vector = models.TfidfModel(bow_vector)[bow_vector]
            model = models.LsiModel(tfidf_vector,
                                    id2word=corpora_dictionary,
                                    num_topics=config.TOPIC_NUMBER)  # 初始化模型
            model_vector = model[tfidf_vector]
            if model_save_path:
                model.save(model_save_path)
        elif model_type == "lda":
            model = models.LdaModel(bow_vector,
                                    id2word=corpora_dictionary,
                                    num_topics=config.TOPIC_NUMBER)  # 初始化模型
            model_vector = model[bow_vector]
            if model_save_path:
                model.save(model_save_path)
        elif model_type == "tfidf":
            model = models.TfidfModel(bow_vector)  # 初始化
            model_vector = model[bow_vector]  # 将整个语料进行转换
            if model_save_path:
                model.save(model_save_path)
        return model_vector

    def add_unseen_documents_to_serialized_model(self,
                                                 old_model_path,
                                                 another_raw_documents_list,
                                                 latest_model_path=None,
                                                 model_type="lsi",
                                                 old_dict_path=None,
                                                 new_dict_path=None,
                                                 corpus_save_path=None):
        loaded_model = None
        model_vector = None
        # 加载已有的模型，Gensim提供在线学习的模式，不断基于新的documents训练新的模型
        if not os.path.exists(old_model_path):
            raise Exception("the file path {} does not exist ... ".format(old_model_path))
        # 根据新的文档或者语料更新原有的词典(没有则构造新词典)
        _, corpora_dictionary, bow_vec = self.create_bag_of_word_representation(another_raw_documents_list,
                                                                                old_dict_path=old_dict_path,
                                                                                new_dict_path=new_dict_path,
                                                                                bow_vector_save_path=corpus_save_path)
        # 加载历史模型
        assert model_type in ["lsi", "lda"]
        if model_type == "lsi":
            loaded_model = models.LsiModel.load(old_model_path)
            another_tfidf_model_vector = self.transform_vectorized_corpus(corpora_dictionary,
                                                                          bow_vec,
                                                                          model_type="tfidf")
            loaded_model.add_documents(another_tfidf_model_vector)
            model_vector = loaded_model[another_tfidf_model_vector]
        elif model_type == "lda":
            loaded_model = models.LdaModel.load(old_model_path)
            loaded_model.update(bow_vec)  # 注意lda和lsi的模型在线更新函数不一样
            model_vector = loaded_model[bow_vec]

        if latest_model_path:
            old_model_path = latest_model_path
        assert loaded_model and model_vector is not None
        loaded_model.save(old_model_path)
        return model_vector

    # def load_transform_model(self, model_path):
    #     if ".tfidf" in model_path:
    #         return models.TfidfModel.load(model_path)
    #     elif ".lsi" in model_path:
    #         return models.LsiModel.load(model_path)
    #     elif ".lda" in model_path:
    #         return models.LdaModel.load(model_path)


if __name__ == "__main__":
    from Hisoka.classifier import Classifier
    from Kite.database import Database
    from sklearn import preprocessing

    database = Database()
    topicmodelling = TopicModelling()
    raw_documents_list = []
    Y = []
    for row in database.get_collection("stocknews", "sz000001").find():
        if "60DaysLabel" in row.keys():
            raw_documents_list.append(row["Article"])
            Y.append(row["60DaysLabel"])
    le = preprocessing.LabelEncoder()
    Y = le.fit_transform(Y)

    _, corpora_dictionary, corpus = topicmodelling.create_bag_of_word_representation(raw_documents_list)
    model_vector = topicmodelling.transform_vectorized_corpus(corpora_dictionary,
                                                              corpus,
                                                              model_type="lsi")
    csr_matrix = utils.convert_to_csr_matrix(model_vector)
    train_x, train_y, test_x, test_y = utils.generate_training_set(csr_matrix, Y)
    classifier = Classifier()
    classifier.svm(train_x, train_y, test_x, test_y)

    # lsi Tue, 15 Dec 2020 14:54:08 classifier.py[line:54] INFO train_pred: 0.9829  test_pred: 0.703 (只是去掉停用词、tab符以及空格符) 30DaysLabel
    # lsi Tue, 15 Dec 2020 17:00:58 classifier.py[line:54] INFO train_pred: 0.9852  test_pred: 0.7492(去掉不含中文的词以及只有一个字符的词) 30DaysLabel
    # lda Tue, 15 Dec 2020 17:29:56 classifier.py[line:54] INFO train_pred: 0.9498  test_pred: 0.7426(去掉不含中文的词以及只有一个字符的词) 30DaysLabel
    # lsi Wed, 16 Dec 2020 15:57:28 classifier.py[line:54] INFO train_pred: 0.9872  test_pred: 0.7478(修改create_dictionary后) 30DaysLabel
    # lsi Wed, 16 Dec 2020 17:14:57 classifier.py[line:54] INFO train_pred: 0.9777  test_pred: 0.7247(修改create_dictionary后) 3DaysLabel
    # lsi Wed, 16 Dec 2020 17:30:15 classifier.py[line:54] INFO train_pred: 0.9883  test_pred: 0.7123(修改create_dictionary后) 60DaysLabel
