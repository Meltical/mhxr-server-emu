# -*- coding: utf-8 -*-

import struct
def tile_pal(pal,tile_x,tile_y):
    #将linear排列的调色板转换为tile排列
    #PSP 恐怖惊魂夜2,女神异闻录3P
    ntx=16/tile_x
    nty=16/tile_y
    i=0
    outpal=[]
    for j in range(256):outpal.append((0,0,0,0))#创建一个空调色板
    for ty in range(nty):
        for tx in range(ntx):
            for y in range(tile_y):
                for x in range(tile_x):
                    outpal[(ty * tile_y + y) * 16 + (tx * tile_x + x)]=pal[i]
                    i+=1
    return outpal
def tile2linear(data,ntx,nty,tile_h,tile_w):
    #将tile图数据重新排列为线性数据
    #PSP图像常用16x8 32x8等
    #部分字库也可以理解为tile图处理 比如14x14 16x16
    #DXT图像为4x4
    width=ntx*tile_w
    height=nty*tile_h
    tilelst=[]
    tile_len=tile_w*tile_h
    for k in range(0,width*height,tile_len):
        tile = data[k:k+tile_len]
        tilelst.append(tile)
    nPixel_data=[]
    for a in range(nty):
        for b in range(tile_h):
            for c in range(ntx):
                for d in range(tile_w):
                    index = a*ntx+c
                    index_tile = b*tile_w+d
                    nPixel_data.append((tilelst[index][index_tile]))
    return nPixel_data
def getPaletteData(paldata,aRange,byte_len,transparency_settings,transparency_index):
    #读取RGBA8888/RGBA4444调色板的颜色值,aRange为alpha范围，0-0xFF，若为256级灰度，则为0xff
    #部分PS2游戏是128级灰度，比如恐怖惊魂夜
    #byte_len==4 RGBA8888调色板
    #byte_len==2 RGBA4444调色板
    #byte_len==3 RGB调色板,无alpha
    #transparency_settings 透明度设定，如果调色板中某一颜色需要设定为透明底色，则为True
    #transparency_index 强制设定调色板中的设定为透明色的颜色索引值，比如第一色为透明，则为0
    #(在transparency_settings为True时本项有效)
    Palette_size=len(paldata)
    rangesize=aRange
    RGBlst=[]
    if byte_len==4:#PALETTE_FORMAT_RGBA8888
        for i in range(0,Palette_size,4):
            (r,g,b,a)=ord(paldata[i]),\
                       ord(paldata[i+1]),\
                       ord(paldata[i+2]),\
                       ord(paldata[i+3])
            a=int(float(0xff)*(float(a)/float(rangesize)))#设定alpha通道范围
            RGBlst.append((r,g,b,a))
    if byte_len==2:#PALETTE_FORMAT_RGBA4444
        for i in range(0,Palette_size,2):
            bt=paldata[i:i+2]
            (r,g,b,a)=((ord(bt[0])&0x0f)<<4,\
                       (ord(bt[0])&0xf0),\
                       (ord(bt[1])&0x0f)<<4,\
                       (ord(bt[1])&0xf0))
            a=int(float(0xff)*(float(a)/float(rangesize)))#设定alpha通道范围
            RGBlst.append((r,g,b,a))
    if byte_len==3:#PALETTE_FORMAT_RGB888,no alpha PSP Black Rock Shooter Font
        for i in range(0,Palette_size,3):
            (r,g,b,a)=(ord(paldata[i]),ord(paldata[i+1]),\
                ord(paldata[i+2]),255)
            RGBlst.append((r,g,b,a))
    if transparency_settings==True:
        (r0,g0,b0,a0)=RGBlst[transparency_index]
        RGBlst[transparency_index]=(r0,g0,b0,0)
    return RGBlst
def findIndexColor(pixelColor, RGBlst, color_num):
    if pixelColor in RGBlst:
        return RGBlst.index(pixelColor)
    else:
        dlist=[]
        (fR,fG,fB,fA)=pixelColor
        for pColor in RGBlst:
            (tR,tG,tB,tA)=pColor
            rMean=(fR * fA + tR * tA)/510
            rDiff = (fR * fA - tR * tA)/255
            gDiff = (fG * fA - tG * tA)/255
            bDiff = (fB * fA - tB * tA)/255
            aDiff = fA - tA
            dist  = (510 + rMean) * (rDiff**2) + \
                    1020 * (gDiff ** 2) + \
                    (765 - rMean) * (bDiff**2) + \
                    1530 * (aDiff**2)
            dlist.append(dist)
            if dist == 0:
                break
        minDist = min(dlist)
        return dlist.index(minDist)
def paint2BPP(width,height,tile_w,tile_h,data_buff,paletteData,Endian_type):
    assert width%tile_w==0, 'set Width/tile Error'
    #width 图片宽度
    #height 图片高度
    #tile_w tile宽度
    #tile_h tile高度
    #data_buff 图像数据区
    #paletteData 调色板列表(list)
    #Endian_type  BIG或者LITTLE
    print(width,height,tile_w,tile_h,len(data_buff))
    if Endian_type=='BIG':
        IsBigEndian=True
    else:
        IsBigEndian=False
    TileSize=(tile_w,tile_h)
    nNecessBytes = width * height/4
    if len(data_buff)<nNecessBytes:
        data_buff+=('\x00'*(nNecessBytes-len(data_buff)))
    ntx = width /TileSize[0] #amount of tiles horizontally
    nty = height /TileSize[1] #amount of tile in vertically
    pixNum = 0
    newdata=''
    nPixels = width *height
    for i in range(nNecessBytes):#Decompress nBPP pixels from DATA 
        bt=ord(data_buff[i])
        for b in range(4):
            if pixNum > nPixels:
                break
            if IsBigEndian:
                j = ((bt & (0x03 << (b * 2))) >> (b * 2))
                newdata+=chr(j)
            else:
                j = ((bt & (0xC0 >> (b * 2))) >> ((3 - b) * 2))
                newdata+=chr(j)
                pixNum+=1
    nPixel_data=tile2linear(newdata,ntx,nty,tile_h,tile_w)
    datalist=[]
    for char in nPixel_data:
        datalist.append(paletteData[char])
    return datalist
def paint4BPP(width,height,tile_w,tile_h,data_buff,paletteData,Endian_type):
    assert width%tile_w==0, 'set Width/tile Error'
    print(width,height,tile_w,tile_h,len(data_buff))
    if Endian_type=='BIG':
        IsBigEndian=True
    else:
        IsBigEndian=False
    TileSize=(tile_w,tile_h)
    nNecessBytes = width * height/2
    if len(data_buff)<nNecessBytes:
        data_buff+=('\x00'*(nNecessBytes-len(data_buff)))
    ntx = width /TileSize[0] #amount of tiles horizontally
    nty = height /TileSize[1] #amount of tile in vertically
    pixNum = 0
    newdata=''
    nPixels = width *height
    for i in range(nNecessBytes):#Decompress nBPP pixels from DATA 
        bt=ord(data_buff[i])
        for b in range(2):
            if pixNum > nPixels:
                break
            if IsBigEndian:
                j = ((bt & (0x0f << (b * 4))) >> (b * 4))
                newdata+=chr(j)
            else:
                j = ((bt & (0xf0 >> (b * 4))) >> ((1 - b) * 4))
                newdata+=chr(j)
                pixNum+=1
    nPixel_data=tile2linear(newdata,ntx,nty,tile_h,tile_w)
    datalist=[]
    for char in nPixel_data:
        
        datalist.append(paletteData[ord(char)])
    return datalist
def paint8BPP(width,height,tile_w,tile_h,data_buff,paletteData,paletteType,pal_tx):
    #width 图片宽度
    #height 图片高度
    #tile_w tile宽度
    #tile_h tile高度
    #data_buff 图像数据区
    #paletteData 调色板列表(list)
    #paletteType  调色板类型，linear或者tile
    #pal_tx 调色板tile宽
    #pal_ty 调色板tile高
    assert width%tile_w==0, 'set Width/tile Error'
    if paletteType.lower()=='tile':
        paletteData=tile_pal(paletteData,pal_tx,pal_ty)
    print(width,height,tile_w,tile_h,len(data_buff))
    TileSize=(tile_w,tile_h)
    nNecessBytes = width * height
    if len(data_buff)<nNecessBytes:
        data_buff+=('\x00'*(nNecessBytes-len(data_buff)))
    ntx = width /TileSize[0] #amount of tiles horizontally
    nty = height /TileSize[1] #amount of tile in vertically
    pixNum = 0
    newdata=''
    nPixels = width *height
    newdata+=data_buff[:nPixels]
    nPixel_data=tile2linear(newdata,ntx,nty,tile_h,tile_w)
    datalist=[]
    for char in nPixel_data:
        datalist.append(paletteData[char])
    return datalist
def paintRGB565(width,height,tile_w,tile_h,data_buff,image_type):#uncomplete
    assert width%tile_w==0, 'set Width/tile Error'
    print(width,height,tile_w,tile_h,len(data_buff))
    TileSize=(tile_w,tile_h)
    nNecessBytes = width * height*2
    if len(data_buff)<nNecessBytes:
        data_buff+=('\x00'*(nNecessBytes-len(data_buff)))
    ntx = width /TileSize[0] #amount of tiles horizontally
    nty = height /TileSize[1] #amount of tile in vertically
    pixNum = 0
    newdata=[]
    nPixels = width *height
    for i in range(0,nNecessBytes,2):#Decompress nBPP pixels from DATA 
        bt=struct.unpack('H',data_buff[i:i+2])[0]
        if pixNum > nPixels:
            break
        (b,g,r,a)=(((bt&0x1f)*255+15)/31,(((bt&0x7e0)>>5)*255+31)/63,(((bt&0xf800)>>11)*255+15)/31,0xff)
        pixNum+=1
        if image_type=='BGR':
            newdata.append((b,g,r,a))
        elif image_type=='RGB':
            newdata.append((r,g,b,a))
        else:
            newdata.append((r,g,b,a))
    nPixel_data=tile2linear(newdata,ntx,nty,tile_h,tile_w)
    return nPixel_data
def paintRGBA4444(width,height,tile_w,tile_h,data_buff,image_type):#uncomplete
    assert width%tile_w==0, 'set Width/tile Error'
    print(width,height,tile_w,tile_h,len(data_buff),image_type)
    TileSize=(tile_w,tile_h)
    nNecessBytes = width * height*2
    if len(data_buff)<nNecessBytes:
        data_buff+=('\x00'*(nNecessBytes-len(data_buff)))
    ntx = width /TileSize[0] #amount of tiles horizontally
    nty = height /TileSize[1] #amount of tile in vertically
    pixNum = 0
    newdata=[]
    nPixels = width *height
    for i in range(0,nNecessBytes,2):#Decompress nBPP pixels from DATA 
        bt=struct.unpack('H',data_buff[i:i+2])[0]
        if pixNum > nPixels:
            break
        (b,g,r,a)=(((bt&0xf0)>>4)*255+7)/15,(((bt&0xf00)>>8)*255+7)/15,\
                   (((bt&0xf000)>>12)*255+7)/15,(((bt&0xf)*255+7)/15)
        if image_type=='ABGR':
            newdata.append((a,b,g,r))
        elif image_type=='RGBA':
            newdata.append((r,g,b,a))
        elif image_type=='BGRA':
            newdata.append((b,r,g,a))
        elif image_type=='ARGB':
            newdata.append((a,r,g,b)) 
        else:
            newdata.append((r,g,b,a))
        pixNum+=1
    nPixel_data=tile2linear(newdata,ntx,nty,tile_h,tile_w)
    return nPixel_data
def paintRGBA5551(width,height,tile_w,tile_h,data_buff,image_type):#uncomplete
    assert width%tile_w==0, 'set Width/tile Error'
    print(width,height,tile_w,tile_h,len(data_buff))
    TileSize=(tile_w,tile_h)
    nNecessBytes = width * height*2
    if len(data_buff)<nNecessBytes:
        data_buff+=('\x00'*(nNecessBytes-len(data_buff)))
    ntx = width /TileSize[0] #amount of tiles horizontally
    nty = height /TileSize[1] #amount of tile in vertically
    pixNum = 0
    newdata=[]
    nPixels = width *height
    for i in range(0,nNecessBytes,2):#Decompress nBPP pixels from DATA 
        bt=struct.unpack('H',data_buff[i:i+2])[0]
        if pixNum > nPixels:
            break
        (b,g,r,a)=(((bt&0x1f)*255+15)/31,(((bt&0x3e0)>>5)*255+15)/31,\
                   (((bt&0x7c00)>>10)*255+15)/31,(((bt&0xf)>>15)*0xff))
        
        if image_type == 'ABGR':
            newdata.append((a,b,g,r))
        elif image_type=='RGBA':
            newdata.append((r,g,b,a))
        elif image_type=='BGRA':
            newdata.append((b,r,g,a))
        elif image_type=='ARGB':
            newdata.append((a,r,g,b)) 
        else:
            newdata.append((r,g,b,a))
        pixNum+=1
    nPixel_data=tile2linear(newdata,ntx,nty,tile_h,tile_w)
    return nPixel_data
def paintRGBA8888(width,height,tile_w,tile_h,data_buff,image_type):#uncomplete
    assert width%tile_w==0, 'set Width/tile Error'
    print(width,height,tile_w,tile_h,len(data_buff),image_type)
    TileSize=(tile_w,tile_h)
    nNecessBytes = width * height*4
    if len(data_buff)<nNecessBytes:
        data_buff+=('\x00'*(nNecessBytes-len(data_buff)))
    ntx = width /TileSize[0] #amount of tiles horizontally
    nty = height /TileSize[1] #amount of tile in vertically
    pixNum = 0
    newdata=[]
    nPixels = width *height
    for i in range(0,nNecessBytes,4):#Decompress nBPP pixels from DATA 
        bt=struct.unpack('4B',data_buff[i:i+4])
        if pixNum > nPixels:
            break
        (r,g,b,a)=(bt[0],bt[1],bt[2],bt[3])
        if image_type=='ABGR':#little endian
            newdata.append((a,b,g,r))
        elif image_type=='RGBA':
            newdata.append((r,g,b,a))
        elif image_type=='BGRA':
            newdata.append((b,g,r,a))
        elif image_type=='ARGB':
            newdata.append((a,r,g,b))
        elif image_type=='GBRA':
            newdata.append((g,b,r,a)) 
        else:
            newdata.append((r,g,b,a))
        pixNum+=1
    nPixel_data=tile2linear(newdata,ntx,nty,tile_h,tile_w)
    datalist=[]
    return nPixel_data
def decodeDXT1(width,height,data,alpha_settings):
    #alpha_settings,DXT1只能表示两种透明度，一种是完全透明,一种是完全不透明,可为alpha_settings设为True(DXT1A)/False(DXT1)
    colorlist=[]
    for block in range(len(data)/8):
        (color0, color1) = struct.unpack("<HH", data[block*8:block*8+4])
        index_data=data[block*8+4:block*8+8]
        #color0,color1使用RGB565方式存储
        red0 = (color0>> 11) & 0x1f
        green0 = ( color0 >> 5 ) & 0x3f
        blue0 = ( color0 & 0x1f )
        red1 = (color1>> 11) & 0x1f
        green1 = ( color1 >> 5 ) & 0x3f
        blue1 = ( color1 & 0x1f )
        (r0,g0,b0)=((red0 << 3),(green0 << 2),(blue0 << 3))
        (r1,g1,b1)=((red1 << 3),(green1 << 2),(blue1 << 3))
        #dxt1 4x4像素为一个压缩单位,color0,color1为色盘,剩余4字节(32bits)为索引区域,每2bit代表一个像素颜色
        #此时2bit可以表示4种颜色变化
        #所以除了color0和color1还可以插值出2种颜色
        #color2=color0*2/3+color1*1/3
        #color3=color1*2/3+color0*1/3
        a0=0xff
        a1=0
        newdata=''
        #4字节代表4x4的tile区域，索引方式类似于2bpp图，先将4字节索引表还原16字节
        #也可以用index_data = index_data >> 2逐个取2bit
        for i in range(4):
            bt=ord(index_data[i])
            for b in range(4):
                j = ((bt & (0x03 << (b * 2))) >> (b * 2))
                newdata+=chr(j)
        for i in range(16):
                index=ord(newdata[i])
                index_c=index
                if index_c==0:#如果索引为0，输出color0
                    (rA,gA,bA,aA)=(r0,g0,b0,a0)
                elif index_c==1:#如果索引为1，输出color1
                    (rA,gA,bA,aA)=(r1,g1,b1,a0)
                elif index_c==2:#如果索引为2，进行插值color2=color0*2/3+color1*1/3
                    if alpha_settings==False:
                        (rA,gA,bA,aA)=((r0*2+r1)/3,(g0*2+g1)/3,(b0*2+b1)/3,a0)
                    else:
                        if color0>color1:
                            (rA,gA,bA,aA)=((r0*2+r1)/3,(g0*2+g1)/3,(b0*2+b1)/3,a0)
                        else:
                            (rA,gA,bA,aA)=((r1+r0)/2,(g1+g0)/2,(b1+b0)/2,a0)
                elif index_c==3:#如果索引为3，进行插值color1*2/3+color0*1/3
                    if alpha_settings==False:(rA,gA,bA,aA)=((r1*2+r0)/3,(g1*2+g0)/3,(b1*2+b0)/3,a0)
                    else:
                        if color0>color1:
                            (rA,gA,bA,aA)=((r1*2+r0)/3,(g1*2+g0)/3,(b1*2+b0)/3,a0)
                        else:
                            (rA,gA,bA,aA)=(0,0,0,a0)
                colorlist.append((rA,gA,bA,aA))
    ntx=width/4
    nty=height/4
    newlist=tile2linear(colorlist,ntx,nty,4,4)#将tile图转换为线性图
    return newlist
def decodeDXT3(width,height,data):
    colorlist=[]
    #DXT3为64bit的alpha索引+64bit DXT1颜色插值，每个4x4tile占16字节
    #############
    #-------------8字节alpha索引，每像素的alpha占4bit------------------
    #每个像素可以有16种alpha值
    # 0   1   2   3
    # 4   5   6   7
    # 8   9   10  11
    #12   13  14  15
    #-------------4字节颜色值，color0和color1--------------------------
    #
    #-------------4字节插值判断,每个像素占2bit,共4种插值结果
    #0=color0,1=color1,2=color0*2/3+color1*1/3,3=color1*2/3+color0*1/3
    #共16字节 128bit
    for block in range(len(data)/16):
        b0 = data[block*16:block*16+16]
        color_index = struct.unpack("<8B", b0[:8])#alpha描述索引
        color0, color1 = struct.unpack("<HH", b0[8:12])
        code = struct.unpack("<I", b0[12:])[0]
        #color0,color1使用RGB565方式存储
        r0 = ((color0 >> 11) & 0x1f) << 3
        g0 = ((color0 >> 5) & 0x3f) << 2
        b0 = (color0 & 0x1f) << 3
        r1 = ((color1 >> 11) & 0x1f) << 3
        g1 = ((color1 >> 5) & 0x3f) << 2
        b1 = (color1 & 0x1f) << 3
        for i in range(16):
            aCode=i/2
            fA=color_index[aCode]
            fA>>=4
            fA*=17
            index_c=(code>>2*i)&3
            if index_c==0:
                (rA,gA,bA,aA)=(r0,g0,b0,fA)
            elif index_c==1:
                (rA,gA,bA,aA)=(r1,g1,b1,fA)
            elif index_c==2:
                (rA,gA,bA,aA)=((2*r0+r1)/3,(2*g0+g1)/3,(b0*2+b1)/3,fA)
            elif index_c==3:
                (rA,gA,bA,aA)=((r1*2+r0)/3,(g1*2+g0)/3,(b1*2+b0)/3,fA)
            colorlist.append((rA,gA,bA,aA))
    ntx=width/4
    nty=height/4
    newlist=tile2linear(colorlist,ntx,nty,4,4)#将tile图转换为线性图
    return newlist
def decodeDXT5(width,height,data):
    #DXT5为64bit的alpha索引+64bit DXT1颜色插值，每个4x4tile占16字节
    #
    #-------------8字节alpha索引，每像素的alpha占4bit------------------
    #头2字节为alpha_0和alpha_1，后6字节为alpha插值索引。每个像素占3bit
    #每个像素可以插值出6种或者8种
    #0=alpha0,1=alpha1,2-5插值,6=0x0完全透明,7=0xff完全不透明
    #6字节alpha插值区域
    # 0   1   2   3
    # 4   5   6   7
    # 8   9   10  11
    #12   13  14  15
    #3bit索引读取方法如下
    #比如索引区为'\xa0\x93\x24\x49\x92\x24'
    #2进制为 10100000,10010011,100100,1001001,10010010,100100
    #索引表为 
    #000,100,110,001,
    #001,001,001,001,
    #001,001,001,001,
    #001,001,001,001,
    #即对应索引表为
    # 0  4   6   1
    # 1  1   1   1
    # 1  1   1   1
    # 1  1   1   1
    #-------------4字节颜色值，color0和color1--------------------------
    #-------------4字节颜色插值判断,每个像素占2bit,共4种插值结果
    colorlist=[]
    for block in range(len(data)/16):
        b0 = data[block*16:block*16+16]
        (a0,a1)=struct.unpack("<BB", b0[:2])
        bits = struct.unpack("<6B", b0[2:8])
        alphaCode1 = bits[2] | (bits[3] << 8) | (bits[4] << 16) | (bits[5] << 24)
        alphaCode2 = bits[0] | (bits[1] << 8)
        color0, color1 = struct.unpack("<HH", b0[8:12])
        code = struct.unpack("<I", b0[12:])[0]
        #color0,color1使用RGB565方式存储
        r0 = ((color0 >> 11) & 0x1f) << 3
        g0 = ((color0 >> 5) & 0x3f) << 2
        b0 = (color0 & 0x1f) << 3
        r1 = ((color1 >> 11) & 0x1f) << 3
        g1 = ((color1 >> 5) & 0x3f) << 2
        b1 = (color1 & 0x1f) << 3
        for i in range(16):
            alphaCodeIndex = 3*i
            if alphaCodeIndex <= 12:
                alphaCode = (alphaCode2 >> alphaCodeIndex) & 0x07
            elif alphaCodeIndex == 15:
                alphaCode = (alphaCode2 >> 15) | ((alphaCode1 << 1) & 0x06)
            else:
                alphaCode = (alphaCode1 >> (alphaCodeIndex - 16)) & 0x07
            if alphaCode == 0:
                fA=a0
            elif alphaCode == 1:
                fA=a1
            else:
                if a0 > a1:
                    fA=((8-alphaCode)*a0+(alphaCode-1)*a1)/7
                else:
                    if alphaCode == 6:
                        fA = 0
                    elif alphaCode == 7:
                        fA = 255
                    else:
                        fA = ((6-alphaCode)*a0+(alphaCode-1)*a1)/5
            index_c=(code >> 2*i) & 3
            if index_c==0:
                (rA,gA,bA,aA)=(r0,g0,b0,fA)
            elif index_c==1:
                (rA,gA,bA,aA)=(r1,g1,b1,fA)
            elif index_c==2:
                (rA,gA,bA,aA)=((2*r0+r1)/3,(2*g0+g1)/3,(b0*2+b1)/3,fA)
            elif index_c==3:
                (rA,gA,bA,aA)=((r1*2+r0)/3,(g1*2+g0)/3,(b1*2+b0)/3,fA)
            colorlist.append((rA,gA,bA,aA))
    ntx=width/4
    nty=height/4
    newlist=tile2linear(colorlist,ntx,nty,4,4)#将tile图转换为线性图
    return newlist

def create2BPP(width,height,tile_w,tile_h,im,paletteData,Endian_type):
    if Endian_type=='BIG':
        IsBigEndian=True
    else:
        IsBigEndian=False
    assert width == im.size[0], 'PNG Width Error'
    assert height == im.size[1], 'PNG Height Error'
    imdata=''
    ntx=width/tile_w
    nty=height/tile_h
    nPixel_data=[]
    tx,ty=0,0
    for a in range(nty):
        for b in range(ntx):
            for c in range(tile_h):
                for d in range(tile_w):
                    (tx,ty)=(d+tile_w*b,c+tile_h*a)
                    nPixel_data.append((im.getpixel((tx,ty))))
    indexlist=[]
    for pixelColor in nPixel_data:
        getIndex=findIndexColor(pixelColor, paletteData, 4)
        indexlist.append(getIndex)
    imdata=''
    for i in range(0,len(indexlist),4):
        if IsBigEndian:
            n=(indexlist[i],indexlist[i+1],indexlist[i+2],indexlist[i+3])
        else:
            n=(indexlist[i+3],indexlist[i+2],indexlist[i+2],indexlist[i])
        bt=0
        for b in range(4):
            bt+=(n[b]<<(b * 2))
        imdata+=chr(bt)
    return imdata
def create4BPP(width,height,tile_w,tile_h,im,paletteData,Endian_type):
    if Endian_type=='BIG':
        IsBigEndian=True
    else:
        IsBigEndian=False
    assert width == im.size[0], 'PNG Width Error'
    assert height == im.size[1], 'PNG Height Error'
    imdata=''
    ntx=width/tile_w
    nty=height/tile_h
    nPixel_data=[]
    tx,ty=0,0
    for a in range(nty):
        for b in range(ntx):
            for c in range(tile_h):
                for d in range(tile_w):
                    (tx,ty)=(d+tile_w*b,c+tile_h*a)
                    nPixel_data.append((im.getpixel((tx,ty))))
    indexlist=[]
    for pixelColor in nPixel_data:
        getIndex=findIndexColor(pixelColor, paletteData, 16)
        indexlist.append(getIndex)
    imdata=''
    for i in range(0,len(indexlist),2):
        if IsBigEndian:n=(indexlist[i],indexlist[i+1])
        else:n=(indexlist[i+1],indexlist[i])
        bt=0
        for b in range(2):
            bt+=(n[b]<<(b * 4))
        imdata+=chr(bt)
    return imdata
def create8BPP(width,height,tile_w,tile_h,im,paletteData,paletteType,pal_tx,pal_ty):
    if paletteType.lower()=='tile':
        paletteData=tile_pal(paletteData,pal_tx,pal_ty)
    assert width == im.size[0], 'PNG Width Error'
    assert height == im.size[1], 'PNG Height Error'
    imdata=''
    ntx=width/tile_w
    nty=height/tile_h
    nPixel_data=[]
    tx,ty=0,0
    for a in range(nty):
        for b in range(ntx):
            for c in range(tile_h):
                for d in range(tile_w):
                    (tx,ty)=(d+tile_w*b,c+tile_h*a)
                    nPixel_data.append((im.getpixel((tx,ty))))
    indexlist=[]
    for pixelColor in nPixel_data:
        getIndex=findIndexColor(pixelColor, paletteData, 256)
        indexlist.append(getIndex)
    imdata=''
    for i in range(len(indexlist)):
        bt=indexlist[i]
        imdata+=chr(bt)
    return imdata
def createRGBA8888(width,height,im,rgbaType):
    #set rgbaType first
    assert width == im.size[0], 'PNG Width Error'
    assert height == im.size[1], 'PNG Height Error'
    imdata=''
    nPixel_data=[]
    for y in range(height):
        for x in range(width):
            (r0,g0,b0,a0)=im.getpixel((x,y))
            if rgbaType=='BGRA':
                fR,fG,fB,fA=(b0,g0,r0,a0)
            else:
                fR,fG,fB,fA=(r0,g0,b0,a0)
            nPixel_data.append((fR,fG,fB,fA))
    for n in nPixel_data:
        (cR,cG,cB,cA)=n
        #print((cR,cG,cB,cA))
        if cA==0:
            (cR,cG,cB,cA)=(0,0,0,0)
        imdata+=(chr(cR)+chr(cG)+chr(cB)+chr(cA))
    return imdata

    