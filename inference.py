import os
import argparse
import datetime

import torch
import torchtext.data as data
import torchtext.datasets as datasets

import model
import train
import mydatasets
import pandas as pd
import numpy as np

''''''
parser = argparse.ArgumentParser(description='CNN text classificer')
# learning

parser.add_argument('-batch-size', type=int, default=16, help='batch size for training [default: 64]')
parser.add_argument('-log-interval',  type=int, default=1,   help='how many steps to wait before logging training status [default: 1]')
parser.add_argument('-test-interval', type=int, default=100, help='how many steps to wait before testing [default: 100]')
parser.add_argument('-save-interval', type=int, default=500, help='how many steps to wait before saving [default:500]')
parser.add_argument('-save-dir', type=str, default='snapshot', help='where to save the snapshot')
parser.add_argument('-early-stop', type=int, default=1000, help='iteration numbers to stop without performance increasing')
parser.add_argument('-save-best', type=bool, default=True, help='whether to save when get best performance')
# data
parser.add_argument('-shuffle', action='store_true', default=False, help='shuffle the data every epoch')
# model
parser.add_argument('-dropout', type=float, default=0.5, help='the probability for dropout [default: 0.5]')
parser.add_argument('-max-norm', type=float, default=3.0, help='l2 constraint of parameters [default: 3.0]')
parser.add_argument('-embed-dim', type=int, default=128, help='number of embedding dimension [default: 128]')
parser.add_argument('-kernel-num', type=int, default=100, help='number of each kind of kernel')
parser.add_argument('-kernel-sizes', type=str, default='3,4,5', help='comma-separated kernel size to use for convolution')
parser.add_argument('-static', action='store_true', default=False, help='fix the embedding')
# device
parser.add_argument('-device', type=int, default=-1, help='device to use for iterate data, -1 mean cpu [default: -1]')
parser.add_argument('-no-cuda', action='store_true', default=False, help='disable the gpu')
# option
parser.add_argument('-snapshot', type=str, default="snapshot/2020-11-03_06-17-04co/best_steps_100.pt", help='filename of model snapshot [default: None]')
parser.add_argument('-predict', type=str, default="나는 오늘 정말 행복해", help='predict the sentence given')
parser.add_argument('-test', action='store_true', default=False, help='train or test')
args = parser.parse_args()

batch_size = 16

def msw_text(text_field, label_field, **kargs):
    train_data, dev_data = mydatasets.MR_2.splits(text_field, label_field)  # 이거로 train_data, test_data를 만드는거

    text_field.build_vocab(train_data, dev_data)  # 단어 집합을 생성
    label_field.build_vocab(train_data, dev_data)

    train_iter, dev_iter = data.Iterator.splits(
                                (train_data, dev_data),
                                batch_sizes=(args.batch_size, len(dev_data)),
                                **kargs)
    '''
    train_iter = data.Iterator(dataset=train_data, batch_size=args.batch_size)
    dev_iter = data.Iterator(dataset=dev_data, batch_size=len(dev_data))
    '''
    print('check Vocabulary', text_field.vocab.stoi)
    print('훈련 데이터의 미니 배치 수 : {}'.format(len(train_iter)))
    print('테스트 데이터의 미니 배치 수 : {}'.format(len(dev_iter)))
    return train_iter, dev_iter


# load data
print("\nLoading data...")
text_field = data.Field(lower=True)
label_field = data.Field(sequential=False)
#train_iter, dev_iter = mr(text_field, label_field, device=-1, repeat=False)
train_iter, dev_iter = msw_text(text_field, label_field, device=-1, repeat=False)

# batch = next(iter(train_iter))
# print(type(batch))
# print(batch.text)

# train_iter, dev_iter, test_iter = sst(text_field, label_field, device=-1, repeat=False)


# update args and print
args.embed_num = len(text_field.vocab) # .vocab을 해주면 단어 집합을 만들어 주는거 같다. 일단 추정
args.class_num = len(label_field.vocab) - 1
args.cuda = (not args.no_cuda) and torch.cuda.is_available(); del args.no_cuda
args.kernel_sizes = [int(k) for k in args.kernel_sizes.split(',')]


print("\nParameters:")
for attr, value in sorted(args.__dict__.items()):
    print("\t{}={}".format(attr.upper(), value))


# model
cnn = model.CNN_Text(args)
if args.snapshot is not None:
    print('\nLoading model from {}...'.format(args.snapshot))
    cnn.load_state_dict(torch.load(args.snapshot))

if args.cuda:
    torch.cuda.set_device(args.device)
    cnn = cnn.cuda()
#----------------------------------------------------------------------------------------------------
input_path  = "datas/asr_output_sample.csv"

#preprocess
pd_input_data = pd.read_csv(input_path)

#model_inference
result = np.zeros((len(pd_input_data), 5))

for i, data in enumerate(pd_input_data[['filename', 'id', 'script']].values):
    script_text = data[2]
    label = train.predict(script_text, cnn, text_field, label_field, args.cuda)
    print('\n[Text]  {}\n[Label] {}\n'.format(script_text, label))
    result[i] = label.cpu().detach().numpy()

print(result)

'''
label = train.predict(args.predict, cnn, text_field, label_field, args.cuda)
print('\n[Text]  {}\n[Label] {}\n'.format(args.predict, label))
'''