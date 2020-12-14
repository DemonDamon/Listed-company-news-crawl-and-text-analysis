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
    topicmodelling = TopicModelling()
    raw_documents_list = [
        "中央、地方支持政策频出,煤炭行业站上了风口 券商研报浩如烟海，投资线索眼花缭乱，\
        第一财经推出《一财研选》产品，挖掘研报精华，每期梳理5条投资线索，便于您短时间内获\
        取有价值的信息。专业团队每周日至每周四晚8点准时“上新”，助您投资顺利！",

        "郭文仓到重点工程项目督导检查 2月2日,公司党委书记、董事长、总经理郭文仓,公司董事,\
        股份公司副总经理、总工程师、郭毅民,股份公司副总经理张国富、柴高贵及相关单位负责人到\
        焦化厂煤场全封闭和干熄焦等重点工程项目建设工地督导检查施工进度和安全工作情况。",

        "负增长在未来会成为一个趋势吗?《新闻1+1》连线国务院发展研究中心宏观经济研究部研究员\
        张立群,共同关注:11月CPI,为何创了11年来的新",

        "为世界人民探寻发展之路提供途径) 首先提两个问题:我们所了解的球星,究竟是真实的他,还是\
        被大众传媒塑造出来的刻板形象?",

        "从黑龙江省牡丹江市政府新闻办获悉,黑龙江省牡丹江市东宁市、绥芬河市各新增1例本土确诊病例",

        "四川新增新型冠状病毒肺炎确诊病例4例(均为本地病例),新增治愈出院病例1例,无新增疑似病例,无\
        新增死亡病例"
    ]
    _, corpora_dictionary, bow_vector = topicmodelling.create_bag_of_word_representation(raw_documents_list)
    # for _vector in bow_vector:
    _, model_vector = topicmodelling.transform_vectorized_corpus(corpora_dictionary,
                                                                 bow_vector,
                                                                 model_type="lsi")
    csr_matrix = utils.convert_to_csr_matrix(model_vector)
    train_x, train_y, test_x, test_y = utils.generate_training_set(csr_matrix, [1, 0, 1, 0, 1, 0])
