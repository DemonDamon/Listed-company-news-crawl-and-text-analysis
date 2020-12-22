import __init__
import os

from Kite import config
from Kite import utils
from Kite.database import Database
from Leorio.tokenization import Tokenization
from Hisoka.classifier import Classifier

from sklearn import preprocessing

from gensim import corpora
from gensim import models
from gensim.matutils import corpus2dense

import logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s",
                    datefmt="%a, %d %b %Y %H:%M:%S")


class TopicModelling(object):

    def __init__(self):
        self.tokenization = Tokenization(import_module="jieba",
                                         user_dict=config.USER_DEFINED_DICT_PATH,
                                         chn_stop_words_dir=config.CHN_STOP_WORDS_PATH)
        self.database = Database()
        self.classifier = Classifier()

    def create_dictionary(self,
                          raw_documents_list,
                          save_path=None,
                          is_saved=False):
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
        if is_saved and save_path:
            _dict.save(save_path)
            logging.info("new generated dictionary saved in path -> {} ...".format(ori_dict_path))

        return _dict, documents_token_list

    def renew_dictionary(self,
                         old_dict_path,
                         new_raw_documents_list,
                         new_dict_path=None,
                         is_saved=False):
        documents_token_list = []
        for doc in new_raw_documents_list:
            documents_token_list.append(self.tokenization.cut_words(doc))
        _dict = corpora.Dictionary.load(old_dict_path)
        _dict.add_documents(documents_token_list)
        if new_dict_path:
            old_dict_path = new_dict_path
        if is_saved:
            _dict.save(old_dict_path)
            logging.info("updated dictionary by another raw documents serialized in {} ... ".format(old_dict_path))

        return _dict, documents_token_list

    def create_bag_of_word_representation(self,
                                          raw_documents_list,
                                          old_dict_path=None,
                                          new_dict_path=None,
                                          bow_vector_save_path=None,
                                          is_saved_dict=False):
        if old_dict_path:
            # 如果存在旧的语料词典，就在原先词典的基础上更新，增加未见过的词
            corpora_dictionary, documents_token_list = self.renew_dictionary(old_dict_path,
                                                                             raw_documents_list,
                                                                             new_dict_path=new_dict_path)
        else:
            # 否则重新创建词典
            corpora_dictionary, documents_token_list = self.create_dictionary(raw_documents_list,
                                                                              save_path=new_dict_path,
                                                                              is_saved=is_saved_dict)
        # 根据新词典对文档(或语料)生成对应的词袋向量
        bow_vector = [corpora_dictionary.doc2bow(doc_token) for doc_token in documents_token_list]
        if bow_vector_save_path:
            corpora.MmCorpus.serialize(bow_vector_save_path, bow_vector)

        return documents_token_list, corpora_dictionary, bow_vector

    @staticmethod
    def transform_vectorized_corpus(corpora_dictionary,
                                    bow_vector,
                                    model_type="lda",
                                    model_save_path=None):
        # 如何没有保存任何模型，重新训练的情况下，可以选择该函数
        model_vector = None
        if model_type == "lsi":
            # LSI(Latent Semantic Indexing)模型，将文本从词袋向量或者词频向量(更好)，转为一个低维度的latent空间
            # 对于现实语料，目标维度在200-500被认为是"黄金标准"
            model_tfidf = models.TfidfModel(bow_vector)
            # model_tfidf.save("model_tfidf.tfidf")
            tfidf_vector = model_tfidf[bow_vector]
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
            # model = models.TfidfModel.load("model_tfidf.tfidf")
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
        # 根据新的文档或者语料更新原有的词典(没有则构造新词典)，此时的bow_vec是根据新的词典计算
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

    @staticmethod
    def load_transform_model(model_path):
        if ".tfidf" in model_path:
            return models.TfidfModel.load(model_path)
        elif ".lsi" in model_path:
            return models.LsiModel.load(model_path)
        elif ".lda" in model_path:
            return models.LdaModel.load(model_path)

    def classify_stock_news(self,
                            unseen_raw_document,
                            database_name,
                            collection_name,
                            label_name="60DaysLabel",
                            topic_model_type="lsi",
                            classifier_model="svm",
                            ori_dict_path=None,
                            bowvec_save_path=None,
                            is_saved_bow_vector=False):
        historical_raw_documents_list = []
        Y = []
        for row in self.database.get_collection(database_name, collection_name).find():
            if label_name in row.keys():
                historical_raw_documents_list.append(row["Article"])
                Y.append(row[label_name])
        logging.info("fetch symbol '{}' historical news with label '{}' from [DB:'{}' - COL:'{}'] ... "
                     .format(collection_name, label_name, database_name, collection_name))

        le = preprocessing.LabelEncoder()
        Y = le.fit_transform(Y)
        logging.info("encode historical label list by sklearn preprocessing for training ... ")
        label_name_list = le.classes_  # ['中性' '利好' '利空'] -> [0, 1, 2]

        # 根据历史新闻数据库创建词典，以及计算每个历史新闻的词袋向量
        _, _, historical_bow_vec = self.create_bag_of_word_representation(historical_raw_documents_list,
                                                                          new_dict_path=ori_dict_path,
                                                                          is_saved_dict=True)
        logging.info("create dictionary of historical news, and serialized in path -> {} ... ".format(ori_dict_path))

        updated_dictionary_with_old_and_unseen_news, unssen_documents_token_list \
            = self.renew_dictionary(ori_dict_path, [unseen_raw_document])

        os.remove(ori_dict_path)  # 删除掉该字典

        unseen_bow_vector = [updated_dictionary_with_old_and_unseen_news.doc2bow(doc_token) for doc_token in
                             unssen_documents_token_list]
        updated_bow_vector_with_old_and_unseen_news = []
        updated_bow_vector_with_old_and_unseen_news.extend(historical_bow_vec)
        updated_bow_vector_with_old_and_unseen_news.extend(unseen_bow_vector)
        # 原先updated_bow_vector_with_old_and_unseen_news是list类型，但是经过下面序列化后重新加载进来的类型是gensim.corpora.mmcorpus.MmCorpus
        if is_saved_bow_vector and bowvec_save_path:
            corpora.MmCorpus.serialize(bowvec_save_path,
                                       updated_bow_vector_with_old_and_unseen_news)  # 保存更新后的bow向量，即包括新旧新闻的bow向量集
        logging.info("combined bow vector(type -> 'list') generated by historical news with unseen bow vector to create a new one ... ")

        if topic_model_type == "lsi":
            updated_tfidf_model_vector = self.transform_vectorized_corpus(updated_dictionary_with_old_and_unseen_news,
                                                                          updated_bow_vector_with_old_and_unseen_news,
                                                                          model_type="tfidf")  # type -> <gensim.interfaces.TransformedCorpus object>
            logging.info("regenerated TF-IDF model vector by updated dictionary and updated bow-vector ... ")

            model = models.LsiModel(updated_tfidf_model_vector,
                                    id2word=updated_dictionary_with_old_and_unseen_news,
                                    num_topics=config.TOPIC_NUMBER)  # 初始化模型
            model_vector = model[updated_tfidf_model_vector]  # type -> <gensim.interfaces.TransformedCorpus object>
            logging.info("regenerated LSI model vector space by updated TF-IDF model vector space ... ")
        elif topic_model_type == "lda":
            model_vector = self.transform_vectorized_corpus(updated_dictionary_with_old_and_unseen_news,
                                                            updated_bow_vector_with_old_and_unseen_news,
                                                            model_type="lda")
            logging.info("regenerated LDA model vector space by updated dictionary and bow-vector ... ")

        # 将gensim.interfaces.TransformedCorpus类型的lsi模型向量转为numpy矩阵
        latest_matrix = corpus2dense(model_vector,
                                     num_terms=model_vector.obj.num_terms).T
        logging.info("transform {} model vector space to numpy.adarray ... ".format(topic_model_type.upper()))

        # 利用历史数据的话题模型向量(或特征)，进一步训练新闻分类器
        train_x, train_y, test_x, test_y = utils.generate_training_set(latest_matrix[:-1, :], Y)
        clf = self.classifier.train(train_x, train_y, test_x, test_y, model_type=classifier_model)
        logging.info("finished training by sklearn {} using latest {} model vector space ... ".format(classifier_model.upper(),
                                                                                                      topic_model_type.upper()))

        label_id = clf.predict(latest_matrix[-1, :].reshape(1, -1))[0]

        return label_name_list[label_id]


if __name__ == "__main__":
    label_name = "60DaysLabel"
    database_name = "stocknews"
    # sh600004的数据量比较少，可作为跑通代码流程的参数；sz000001的数据量比较大，处理起来也较慢，可以作为后续案例测试
    collection_name = "sh600004"
    classifier_save_path = "{}_classifier.pkl".format(collection_name)
    ori_dict_path = "{}_docs_dict.dict".format(collection_name)
    bowvec_save_path = "{}_bowvec.mm".format(collection_name)

    # 对(未见过的)新闻进行分类
    unseen_raw_documents_list = ["本案的当事人孙某，现年57岁，家住辽宁大连。自2014年起，孙某就开始在平\
                                  安银行(18.830, -0.12, -0.63%)大连分行（以下简称“平安银行”）购买金\
                                  融理财产品。证据显示，早在2014年1月16日，经过平安银行的风险测评，孙某\
                                  被评估为平衡型的投资者，风险评估报告由孙某和平安银行的理财经理共同签字\
                                  。之后，孙某一直通过理财经理购买风险评级低、年化收益率也较低的理财产品。",
                                 "关于公司向平安银行(18.850, -0.10, -0.53%)申请1亿元综合授信额度的议案。\
                                 同意公司向平安银行股份有限公司乌鲁木齐分行申请综合授信额度人民币1亿元，期\
                                 限一年，本次授信由新疆天富集团有限责任公司提供连带责任保证担保。",
                                 "平安银行(18.850, -0.10, -0.53%)荣获第十八届财经风云榜“2020年度金融科技\
                                 创新奖” 来源：和讯银行12月16日，由和讯网主办的2020年财经中国年会暨第十八\
                                 届财经风云榜银行峰会在京召开，会上重磅揭晓第十八届中国财经风云榜之银行业评\
                                 选结果。科技赋能服务创新，平安银行获评“2020年度金融科技创新奖”。"]

    topicmodelling = TopicModelling()
    for unseen_doc in unseen_raw_documents_list:
        chn_label = topicmodelling.classify_stock_news(unseen_doc,
                                                       database_name,
                                                       collection_name,
                                                       label_name=label_name,
                                                       topic_model_type="lsi",
                                                       classifier_model="rdforest",  # rdforest / svm
                                                       ori_dict_path=ori_dict_path,
                                                       bowvec_save_path=bowvec_save_path)
        logging.info("document '{}...' was classified with label '{}' for symbol {} ... ".format(unseen_doc[:20], chn_label, collection_name))

    # lsi Tue, 15 Dec 2020 14:54:08 classifier.py[line:54] INFO train_pred: 0.9829  test_pred: 0.703 (只是去掉停用词、tab符以及空格符) 30DaysLabel
    # lsi Tue, 15 Dec 2020 17:00:58 classifier.py[line:54] INFO train_pred: 0.9852  test_pred: 0.7492(去掉不含中文的词以及只有一个字符的词) 30DaysLabel
    # lda Tue, 15 Dec 2020 17:29:56 classifier.py[line:54] INFO train_pred: 0.9498  test_pred: 0.7426(去掉不含中文的词以及只有一个字符的词) 30DaysLabel
    # lsi Wed, 16 Dec 2020 15:57:28 classifier.py[line:54] INFO train_pred: 0.9872  test_pred: 0.7478(修改create_dictionary后) 30DaysLabel
    # lsi Wed, 16 Dec 2020 17:14:57 classifier.py[line:54] INFO train_pred: 0.9777  test_pred: 0.7247(修改create_dictionary后) 3DaysLabel
    # lsi Wed, 16 Dec 2020 17:30:15 classifier.py[line:54] INFO train_pred: 0.9883  test_pred: 0.7123(修改create_dictionary后) 60DaysLabel
