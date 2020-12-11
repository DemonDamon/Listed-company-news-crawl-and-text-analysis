import __init__

from Kite import config
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
                                         user_dict="../Leorio/financedict.txt",
                                         chn_stop_words_dir="../Leorio/chnstopwords.txt")

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

    def CallTransformationModel(dictionary,bowvec,modelType=kwarg['modelType'],\
			tfDim=kwarg['tfDim'],renewModel=kwarg['renewModel'],modelPath=self.DictPath+'\\'+stockCode+'\\')

    def transform_vectorized_corpus(self,
                                    corpora_dictionary,
                                    bow_vector,
                                    model_type="lda",
                                    lsi_model_save_path=None,
                                    lda_model_save_path=None,
                                    tfidf_model_save_path=None):
        tfidf_model = models.TfidfModel(bow_vector)  # 初始化
        tfidf_vector = tfidf_model[bow_vector]  # 将整个语料进行转换
        if tfidf_model_save_path:
            tfidf_model.save(tfidf_model_save_path)
        if model_type == "lsi":
            model = models.LsiModel(tfidf_vector, id2word=corpora_dictionary, num_topics=config.TOPIC_NUMBER)  # 初始化模型
            model_vector = model[tfidf_vector]
            if lsi_model_save_path:
                model.save(lsi_model_save_path)
        elif model_type == "lda":
            model = models.LdaModel(tfidf_vector, id2word=corpora_dictionary, num_topics=config.TOPIC_NUMBER)  # 初始化模型
            model_vector = model[tfidf_vector]
            if lda_model_save_path:
                model.save(lda_model_save_path)
        else:
            model_vector = tfidf_vector
        return tfidf_vector, model_vector


if __name__ == "__main__":
    topicmodelling = TopicModelling()
    raw_documents_list = [
        "中央、地方支持政策频出,煤炭行业站上了风口 券商研报浩如烟海，投资线索眼花缭乱，\
        第一财经推出《一财研选》产品，挖掘研报精华，每期梳理5条投资线索，便于您短时间内获\
        取有价值的信息。专业团队每周日至每周四晚8点准时“上新”，助您投资顺利！",
        "郭文仓到重点工程项目督导检查 2月2日,公司党委书记、董事长、总经理郭文仓,公司董事,\
        股份公司副总经理、总工程师、郭毅民,股份公司副总经理张国富、柴高贵及相关单位负责人到\
        焦化厂煤场全封闭和干熄焦等重点工程项目建设工地督导检查施工进度和安全工作情况。"
    ]
    print(topicmodelling.create_bag_of_word_representation(raw_documents_list))
