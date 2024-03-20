
**UPDATE**: *This project was finished and turned into a set of custom ComfyUI nodes for easy use* — [found here](https://github.com/christian-byrne/elimination-nodes?tab=readme-ov-file#infinite-parallax-nodes)

# Infinite Parallax

In Unity, *infinite parallax* ([see example](https://www.youtube.com/watch?v=MEy-kIGE-lI)) is a technique used to create the illusion of depth in 2D games. This is done by moving the background layers at different speeds which vary inversely with distance-from-viewer, creating a [parallax](https://en.wikipedia.org/wiki/Parallax) effect.

In the realm of AI image generation, *infinite zoom* ([see example](https://www.youtube.com/watch?v=yDCUTyZD--E)) is a technique used to create the illusion of an infinite zoom, by taking an image, shrinking it, inpainting the padding around it to match the original size, repeating the process, and then stitching the images together into a video using linear [zoom transitions](https://www.youtube.com/watch?v=G01V09CWTJY&t=1s) and, finally, reversing it.

This project combines these ideas. Instead of iteratively shrinking an image and inpainting the padding border, the image is segmented into objects and base layers and each object/layer is shifted in accordance with a given vector of motion. The layers are re-composited after being shifted and the gaps of empty space created by the shifting are inpainted side-by-side. This way, the inpainting process uses the context according to each layer's position at that given time. With a high number of inpainting steps per second, the layers can move at different speeds without totally disrupting the logical flow of the picture. Finally, the layer frames are stitched using linear [sliding transitions](https://www.youtube.com/shorts/S6Ywp-598HI) instead of zoom transitions and the segmented objects are re-composited. See demo below. 

## Examples


**Input Image**

![Johan_Christian_Dahl_-_View_of_Dresden_by_Moonlight](docs/demo/1600px-Johan_Christian_Dahl_-_View_of_Dresden_by_Moonlight_-_Google_Art_Project.jpg)

*View of Dresden by Moonlight* by Johan Christian Dahl

**Output Video**


![Johan_Christian_Dahl_-_View_of_Dresden_by_Moonlight-Infinite_Parallax](projects/example-dresden/output/dresden-final_parallax_video.gif)

Angle of Motion 180°, Layers: 5 (clouds, sky, horizon, midground, foreground), Objects: 1 (Dresden Frauenkirche - domed building) Smoothness: 12, FPS: 30, [Config File](projects/example-dresden/config.json), [Generated Dir](projects/example-dresden)

## Process

[Process Outline and Explanation](docs/process_explanation.md)


## TODO

- [x] Large number of objects testing
- [x] Update current input-image between object extraction steps in order to iteratively remove objects and inpaint negative space
- [x] Expand mask with feathering and blur before extracting alpha layer
- [x] Salient objects
  - [x] Segmentation prompt tags use correct separator/format
  - [x] Multiple iterations of salient object removal
  - [x] Get salient object tags/prompts in config creation
  - [x] Segment
  - [x] Create masks
  - [x] Extract alpha layer
  - [x] Inpaint new base layer and set as new start image
  - [x] Calculate motion vectors for each object alpha layer
    - [x] Determine object velocity from config (default: objects move according to their base layer, option: objects are static or barely move so as to highlight them)
  - [x] Overlay alpha layers onto final video
- [x] Segmentation for initial layers
  - [x] Edit methods to handle non-rectangular layers (CompositeVideoClip)
  - [x] Documentation
- [x] Depth Maps (edit: part of workflow now) 
- [x] ControlNet edge softening (edit: part of workflow now)
- [x] Use project-specific I/O directories
  - [x] As args when starting detached comfy process/server
  - [x] Use filename prefix constants for faster selection of output when server terminates
- [x] Feathering layers on axis perpindicular of motion (e.g. if motion is horizontal, feathering is vertical). Somehow determine how to expand-feather at some poitn in the process before given to `CompositeVideoClip`
- [ ] Full Vector testing
  - [x] Negative and positive velocity testing
- [x] Inpainting prompts (negative and positive) from config
  - [x] For salient object removal
  - [x] For layer shifts
- [x] Delete first image from each layer sequence or don't save in first place
- [x] Auomate video post-processing
  - [x] Add sound from library
  - [x] Color correction
- [x] Auto create reversed version and ping-ponged version after export
- [x] Finalize
  - [x] Create simple example project
  - [x] Update README
  - [x] Turn into ComfyUI node

## Reminders

- A new comfy instance is not started if already running, but the running instance may have been started by user and therefore have different i/o directory args
- Use the non-API workflows for editing manually otherwise you have to re-set the node titles each time
- LoadImage nodes use relative paths from `--input-directory`
- Smoothness is a function of perceivability of pixel distance

