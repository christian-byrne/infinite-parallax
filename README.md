
# Infinite Parallax

In Unity, *infinite parallax* ([see example](https://www.youtube.com/watch?v=MEy-kIGE-lI)) is a technique used to create the illusion of depth in 2D games. This is done by moving the background layers at different speeds which vary inversely with distance-from-viewer, creating a [parallax](https://en.wikipedia.org/wiki/Parallax) effect.

In the realm of AI image generation, *infinite zoom* ([see example](https://www.youtube.com/watch?v=yDCUTyZD--E)) is a technique used to create the illusion of an infinite zoom, by taking an image, shrinking it, inpainting the padding around it to match the original size, repeating the process, and then stitching the images together into a video using linear [zoom transitions](https://www.youtube.com/watch?v=G01V09CWTJY&t=1s) and, finally, reversing it.

This project combines these ideas. Instead of iteratively shrinking an image and inpainting the padding border, the image is sliced into layers and each layer is shifted in accordance with a given vector of motion. The layers are re-composited after being shifted and the gaps of empty space created by the shifting are inpainted side-by-side. This way, the inpainting process uses the context according to each layer's position at that given time. With a high number of inpainting steps per second, the layers can move at different speeds without totally disrupting the logical flow of the picture. Finally, the layer frames are stitched using linear [sliding transitions](https://www.youtube.com/shorts/S6Ywp-598HI) instead of zoom transitions. See demo below. 

## Demo

**Input Image**

![Johan_Christian_Dahl_-_View_of_Dresden_by_Moonlight](docs/demo/1600px-Johan_Christian_Dahl_-_View_of_Dresden_by_Moonlight_-_Google_Art_Project.jpg)

*View of Dresden by Moonlight* by Johan Christian Dahl

**Output Video**

![Johan_Christian_Dahl_-_View_of_Dresden_by_Moonlight-Infinite_Parallax](docs/demo/demo-dresden-parallax.gif)

Angle of Motion: 160°, Layers: 4 (clouds, horizon, background, foreground), Smoothness: 117.5, FPS: 10

*Low quality, bad color conversion, and short length are just products of requiring a gif for github markdown compiler. In the full video, the parallax effect goes until the entire original image is gone*

## Process

[Process Outline and Explanation](docs/process_explanation.md)

## TODO

- [ ] Segmentation for non-rectangular initial layers to solve disjointedness in the shifted initial layers after they've been shifted many steps but are still in the frame (havent fully panned out of the frame yet) 
  - [ ] Segment salient objects -> create masks -> mask from original picture -> overlay onto final video with motion equal to the average of the motion on the layers the object overlaps onto (the purpose being that the salient object is getting disjointed as the the multiple layers its in are moving at different speeds)
  - [ ] Edit methods to handle non-rectangular layers (CompositeVideoClip)
- [ ] Feathering layers on axis perpindicular of motion (e.g. if motion is horizontal, feathering is vertical). Somehow determine how to expand-feather at some poitn in the process before given to `CompositeVideoClip`
- [ ] Full Vector testing
  - [ ] negative velocity testing
- [ ] Delete first image from each layer sequence or don't save in first place
- [ ] Auomate video post-processing
  - [ ] Add sound from library
  - [ ] Color correction
- [ ] Sizing standardization solution from tensorflow to PIL
  - [ ] Crop `ERROR_MARGIN` pixels from top of first layer and bottom of last layer 
- [ ] Create simple example project
- [ ] Update README
- [ ] Turn into ComfyUI node