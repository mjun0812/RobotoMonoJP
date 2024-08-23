# Roboto Mono JP

![Preview](doc/images/font_preview.png)

このフォントは，Roboto MonoとIBM Plex Sans JPを合成し，
Nerd Font Patcherを適用したものです．

同梱している各フォントは配布元のライセンス表記に従います．

Download: https://github.com/mjun0812/RobotoMonoJP/releases

オリジナルのRobotoMonoのサイズに合わせた`RobotoMonoJP`と、
全角文字の幅を2048, 半角文字の幅を1024に合わせた`RobotoMonoJP-Mono`があります。

## Build

```bash
git clone https://github.com/mjun0812/RobotoMonoJP.git
cd RobotoMonoJP
docker build -t robotomonojp .
docker run --rm -it -v ./:/app -w /app robotomonojp python main.py
docker run --rm -it -v ./:/app -w /app robotomonojp python main_mono.py
```

## 参考

- [SF Mono を使って最高のプログラミング用フォントを作った話 - Qiita](https://qiita.com/delphinus/items/f472eb04ff91daf44274)
- [yanoasis/nerd-fonts](https://github.com/ryanoasis/nerd-fonts)
- [IBM/plex](https://github.com/IBM/plex)
- [Google Fonts](https://fonts.google.com/specimen/Roboto+Mono)
- [RobotoMonoに日本語を合成したフォントを作りました](https://note.mjunya.com/posts/2021-12-28-roboto-mono-jp/)
- [プログラミング用フォント Utatane](https://github.com/nv-h/Utatane/blob/master/utatane.py)
- [プログラミング用合成フォント PleckJP を作った](https://ryota2357.com/blog/2023/dev-font-pleckjp/)
- [プログラミング用合成フォント PleckJP の合成スクリプトの実装解説](https://ryota2357.com/blog/2023/pleck-jp-impl-exp/)
- [ryota2357/PleckJP](https://github.com/ryota2357/PleckJP)
