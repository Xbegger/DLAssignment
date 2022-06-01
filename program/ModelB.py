import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import os
from torchvision import datasets, transforms
import numpy as np
import cv2

from dataLoadForMyModel import trainloaderForPhotoB, trainloaderForSketchB, testloaderForPhotoB, testloaderForSketchB

# 判断使用CPU训练还是GPU训练
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# 设置训练数据集的轮次
EPOCHS = 10
# 设置学习率
learning_rate = 1e-5

# 设置每个分类任务的名称
labels = ['skin color', 'lip color', 'eye color', 'hair', 'hair color', 'gender', 'earring', 'smile', 'frontal face',
          'style']
# 设置每个分类任务的类别总数
labelNum = [2, 3, 3, 2, 5, 2, 2, 2, 2, 3]


# 网络模型
class Digit(nn.Module):
    def __init__(self, labelNum):
        super().__init__()
        # 二维卷积层1
        self.conv1 = nn.Sequential(
            nn.BatchNorm2d(3),  # 批归一化
            nn.Conv2d(3, 10, 5, padding=2),  # 3：图片输入通道为3，10：输出通道，5：5*5卷积核
            nn.BatchNorm2d(10),  # 批归一化
            nn.LeakyReLU()  # 激活函数
        )
        # 二维卷积层2_1
        self.conv2_1 = nn.Sequential(
            nn.Conv2d(10, 20, 3, padding=1),  # 10：输入通道，20：输出通道，3：3*3卷积核
            nn.BatchNorm2d(20),  # 批归一化
            nn.LeakyReLU()
        )
        # 二维卷积层2_2
        self.conv2_2 = nn.Sequential(
            nn.Conv2d(20, 80, 3, padding=1),  # 20：输入通道，80：输出通道，3：3*3卷积核
            nn.BatchNorm2d(80),  # 批归一化
            nn.LeakyReLU()
        )
        # 二维卷积层3
        self.conv3 = nn.Sequential(
            nn.Conv2d(20, 20, 3, padding=1),  # 20：输入通道，20：输出通道，3：3*3卷积核
            nn.BatchNorm2d(20),  # 批归一化
            nn.LeakyReLU()
        )
        # 二维卷积层4
        self.conv4 = nn.Sequential(
            nn.Conv2d(80, 20, 3, padding=1),  # 80：输入通道，160：输出通道，3：3*3卷积核
            nn.BatchNorm2d(20),  # 批归一化
            nn.LeakyReLU()
        )
        # 全连接层1
        self.fc1 = nn.Linear(20 * 64 * 64, 2000)  # 20*64*64：输入通道，2000：输出通道
        # 全连接层2
        self.fc2 = nn.Linear(2000, 200)  # 2000：输入通道，200：输出通道
        # 全连接层3
        self.fc3 = nn.Linear(200, labelNum)  # 200：输入通道，labelNum：输出通道

    def forward(self, x, labelNum):
        input_size = x.size(0)  # 其实就是batch_size

        x = self.conv1(x)  # 输入：batch_size*3*256*256，输出：batch_size*10*256*256
        x = F.max_pool2d(x, 2, 2)  # 池化层（数据压缩，降采样），输入：batch_size*10*256*256，输出：batch_size*10*128*128

        x = self.conv2_1(x)  # 输入：batch_size*10*128*128，输出：batch_size*20*128*128
        x = self.conv2_2(x)  # 输入：batch_size*20*128*128，输出：batch_size*80*128*128

        # 残差模块1
        x1 = self.conv4(x)  # 输入：batch_size*20*128*128，输出：batch_size*20*128*128
        x2 = self.conv3(x1)  # 输入：batch_size*20*128*128，输出：batch_size*20*128*128
        x3 = self.conv3(x2)  # 输入：batch_size*20*128*128，输出：batch_size*20*128*128
        x4 = self.conv3(x3)  # 输入：batch_size*20*128*128，输出：batch_size*20*128*128
        x = torch.cat([x1, x2, x3, x4], dim=1)

        # 残差模块2
        x1 = self.conv4(x)  # 输入：batch_size*80*128*128，输出：batch_size*20*128*128
        x2 = self.conv3(x1)  # 输入：batch_size*20*128*128，输出：batch_size*20*128*128
        x3 = self.conv3(x2)  # 输入：batch_size*20*128*128，输出：batch_size*20*128*128
        x4 = self.conv3(x3)  # 输入：batch_size*20*128*128，输出：batch_size*20*128*128
        x = torch.cat([x1, x2, x3, x4], dim=1)

        # 残差模块3
        x1 = self.conv4(x)  # 输入：batch_size*80*128*128，输出：batch_size*20*128*128
        x2 = self.conv3(x1)  # 输入：batch_size*20*128*128，输出：batch_size*20*128*128
        x3 = self.conv3(x2)  # 输入：batch_size*20*128*128，输出：batch_size*20*128*128
        x4 = self.conv3(x3)  # 输入：batch_size*20*128*128，输出：batch_size*20*128*128
        x = torch.cat([x1, x2, x3, x4], dim=1)

        # 残差模块4
        x1 = self.conv4(x)  # 输入：batch_size*80*128*128，输出：batch_size*20*128*128
        x2 = self.conv3(x1)  # 输入：batch_size*20*128*128，输出：batch_size*20*128*128
        x3 = self.conv3(x2)  # 输入：batch_size*20*128*128，输出：batch_size*20*128*128
        x4 = self.conv3(x3)  # 输入：batch_size*20*128*128，输出：batch_size*20*128*128
        x = torch.cat([x1, x2, x3, x4], dim=1)

        x = self.conv4(x)  # 输入：batch_size*80*128*128，输出：batch_size*20*128*128
        x = F.max_pool2d(x, 2, 2)  # 池化层（数据压缩，降采样），输入：batch_size*20*128*128，输出：batch_size*20*64*64

        x = x.view(input_size, -1)  # 降维到1维，-1：自动计算原始维度

        x = self.fc1(x)  # 输入：batch_size*20*64*64，输出：batch_size*2000
        x = F.relu(x)  # 激活函数,保持形状不变，输出：batch_size*2000

        x = self.fc2(x)  # 输入：batch_size*2000，输出：batch_size*200
        x = F.relu(x)  # 激活函数,保持形状不变，输出：batch_size*200

        x = self.fc3(x)  # 输入：batch_size*200，输出：batch_size*labelNum
        output = F.log_softmax(x, dim=1)  # 计算分类后每个数字的概率值，dim=1：按行
        return output


def train_model(model, device, train_loader, optimizer, epoch, labelNO):
    # 模型训练
    model.train()
    for batch_index, (data, label) in enumerate(train_loader):
        label = label[labelNO]
        # 部署到DEVICE上
        data, label = data.to(device), label.to(device)
        # 初始化梯度为0
        optimizer.zero_grad()
        # 训练结果
        output = model(data, labelNum[labelNO])
        # 计算损失
        loss = F.cross_entropy(output, label)
        # 反向传播
        loss.backward()
        # 参数更新
        optimizer.step()
        # 查看损失
        if batch_index % 3000 == 0:
            print("Train Epoch:{}\t Loss:{:.6f}".format(epoch, loss.item()))


def test_model(model, device, test_loader, labelNO):
    # 模型验证
    model.eval()
    # 正确率
    correct = 0.0
    # 测试损失
    test_loss = 0.0
    # 进行测试
    with torch.no_grad():
        labelName = labels[labelNO]
        for data, label in test_loader:
            label = label[labelNO]
            # 部署到DEVICE上
            data, label = data.to(device), label.to(device)
            # 测试数据
            output = model(data, labelNum[labelNO])
            # 计算测试损失
            test_loss += F.cross_entropy(output, label)
            # 找到概率最大的下标
            pred = output.max(1, keepdim=True)[1]  # 返回值格式为（值，索引）
            # 统计正确率
            correct += pred.eq(label.view_as(pred)).sum().item()
        test_loss /= len(test_loader.dataset)
        correct /= len(test_loader.dataset)
        print("Test —— Average Loss:{:.4f}, 标签{}的准确率为{:.3f}%".format(
            test_loss, labelName, correct * 100))
        return correct * 100


# 调用训练方法
def trainAndTest(labelNo, type, result):
    for epoch in range(1, EPOCHS + 1):
        model = Digit(labelNum[labelNo]).to(DEVICE)
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        if type == 'photo':
            train_model(model, DEVICE, trainloaderForPhotoB, optimizer, epoch, labelNo)
            correct = test_model(model, DEVICE, testloaderForPhotoB, labelNo)
            if epoch == EPOCHS:
                result.append({'数据类型': 'photo', '分类用的标签': labels[labelNo], '分类正确率': correct})
        elif type == 'sketch':
            train_model(model, DEVICE, trainloaderForSketchB, optimizer, epoch, labelNo)
            correct = test_model(model, DEVICE, testloaderForSketchB, labelNo)
            if epoch == EPOCHS:
                result.append({'数据类型': 'sketch', '分类用的标签': labels[labelNo], '分类正确率': correct})
        else:
            print('this type of dataset is not exist!')


if __name__ == '__main__':
    labelsToUse = [3, 4, 5, 6, 7, 8, 9]
    types = ['photo', 'sketch']
    result = []
    for type in types:
        for label in labelsToUse:
            trainAndTest(label, type, result)
    s = ''
    for item in result:
        for (key, value) in item.items():
            s = s + key + ':' + str(value) + ' '
        s += '\n'
    print(s)
