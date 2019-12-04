import csv
import os, sys
import argparse

sys.path.append(os.path.join(os.path.dirname(__file__), 'site-packages'))

import MeCab
from wordcloud import WordCloud
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.font_manager as fm

FONT = '/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc'
STOP_WORDS = [
  'てる', 'いる', 'なる', 'れる', 'する', 'ある', 'こと', 'これ', 'さん', 'して',
  'くれる', 'やる', 'くださる', 'そう', 'せる', 'した',
  'それ', 'ここ', 'ちゃん', 'くん', '', 'て','に','を','は','の', 'が', 'と', 'た', 'し', 'で',
  'ない', 'も', 'な', 'い', 'か', 'ので', 'よう', 'あり','',
  'ホテル', '利用']

def mecab_tagger():
  return MeCab.Tagger ('-d /usr/local/lib/mecab/dic/mecab-ipadic-neologd')

def mecab_analysis(text):
  t = mecab_tagger()
  t.parse('')
  output = []

  node = t.parseToNode(text)
  while(node):
    if node.surface != '':  # ヘッダとフッタを除外
      res = node.feature.split(',')
      word_type = res[0]
      #if word_type in ['形容詞', '動詞', '名詞', '副詞']:
      if word_type in ['形容詞', '名詞', '動詞']:
        basic_word = res[6]
        if basic_word != "*":
          output.append(node.surface)
    node = node.next
    if node is None:
        break
  return output

def create_wordcloud(text, yado_no):
  wordcloud = WordCloud(
    background_color='white',
    font_path=FONT,
    stopwords=set(STOP_WORDS),
    width=800,
    height=600).generate(text)

  wordcloud.to_file(f'./wordcloud_{yado_no}.png')

def clustering(text_list):
  k = 4

  # see https://qiita.com/yuuki_1204_/items/3c0a298a521dc6e79615
  # TF-IDFの処理クラス
  vectorizer = TfidfVectorizer(
    min_df=1, stop_words=STOP_WORDS, tokenizer=mecab_analysis)
  # データのベクトル化
  tfidf_weighted_matrix = vectorizer.fit_transform(text_list)

  # k-means
  model = KMeans(n_clusters=k)
  model.fit(tfidf_weighted_matrix)
  # 2次元に圧縮 潜在意味解析(LSA)
  dim = TruncatedSVD(2)
  compressed_text_list = dim.fit_transform(tfidf_weighted_matrix)
  compressed_center_list = dim.fit_transform(model.cluster_centers_)

  # 描画
  FP = fm.FontProperties(fname=FONT, size=7)
  fig = plt.figure()
  axes = fig.add_subplot(111)
  # 3クラスタ
  for label in range(k):
    # ラベルごとに色を分ける
    color = cm.cool(float(label) / k)

    # ラベルの中心をプロット
    xc, yc = compressed_center_list[label]
    axes.plot(xc, yc,
              color=color,
              ms=6.0, zorder=3, marker='o')

    # クラスタのラベルもプロット
    axes.annotate(label, xy=(xc, yc), fontproperties=FP)

    for text_num, text_label in enumerate(model.labels_):
      if text_label == label:
        # labelが一致するテキストをプロット
        x, y = compressed_text_list[text_num]
        axes.plot(x, y,
                  color=color,
                  ms=5.0, zorder=2, marker="x")

        # テキストもプロット
        axes.annotate(text_list[text_num][:8], xy=(x, y), fontproperties=FP)

        # ラベルの中心点からの線をプロット
        axes.plot([x, xc], [y, yc],
                  color=color,
                  linewidth=0.5, zorder=1, linestyle="--")

  plt.axis('tight')
  plt.show()


def main(yado_no):
  path = os.path.join(os.path.dirname(__file__), f'../review/kuchikomi_{yado_no}.csv')
  csv_file = open(path, 'r', encoding='utf8', errors='', newline='')
  f = csv.reader(csv_file, delimiter=',', doublequote=True, lineterminator="\r\n", quotechar='"', skipinitialspace=True)

  text = ''
  text_list = []
  for row in f:
    text = text + ' ' + row[3] + ' ' + row[4]
    text_list.append(row[3] + ' ' + row[4])

  words = mecab_analysis(text)
  print('words done')
  create_wordcloud(' '.join(words), yado_no)
  print('wordcloud donne')
  clustering(text_list)
  print('clustering done')

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--yado_no', help="please set me", type=str)
  args = parser.parse_args()

  if args.yado_no == '':
    print('usage: python mining.py --yado_no 1234')
    exit()

  main(args.yado_no)
