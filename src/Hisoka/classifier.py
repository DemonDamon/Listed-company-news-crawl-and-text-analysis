import __init__
import logging
import warnings

from Kite import config

from sklearn import svm
from sklearn.ensemble import RandomForestClassifier
from sklearn.externals import joblib
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report
import sklearn.exceptions

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s",
                    datefmt="%a, %d %b %Y %H:%M:%S")


class Classifier(object):

    def __init__(self):
        self.tuned_parameters = config.SMV_TUNED_PARAMTERS
        self.scores = config.SMV_SCORE_LIST

    def svm(self, train_x, train_y, test_x, test_y, svm_save_path=None):
        for score in self.scores:
            # 构造这个GridSearch的分类器,5-fold
            clf = GridSearchCV(svm.SVC(), self.tuned_parameters, cv=5, scoring='%s_weighted' % score)
            # 只在训练集上面做k-fold,然后返回最优的模型参数
            clf.fit(train_x, train_y)
            if svm_save_path is not None:
                joblib.dump(svm_save_path)
            # 输出最优的模型参数
            logging.info("the best params: {}".format(clf.best_params_))
            train_pred = clf.predict(train_x)
            test_pred = clf.predict(test_x)  # 在测试集上测试最优的模型的泛化能力
            logging.info(classification_report(test_y, test_pred))

            precise_train = 0
            for k in range(len(train_pred)):
                if train_pred[k] == train_y[k]:
                    precise_train += 1
            precise_test = 0
            for k in range(len(test_pred)):
                if test_pred[k] == test_y[k]:
                    precise_test += 1
            logging.info('train_pred: {}  test_pred: {}'
                         .format(str(round(precise_train / len(train_y), 4)),
                                 str(round(precise_test / len(test_pred), 4))))
            self._precise = precise_test / len(test_pred)

    def rd_forest(self):
        pass