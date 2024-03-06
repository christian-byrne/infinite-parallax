

class SalientObjectLayer(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, stride, padding, dilation, groups, bias):
        super(SalientObjectLayer, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding, dilation, groups, bias)
        self.relu = nn.ReLU(inplace=True)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.conv(x)
        x = self.relu(x)
        x = self.sigmoid(x)
        return x