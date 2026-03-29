# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import collections
from typing import Iterable, Sequence

import numpy as np
import pygltflib


class ColoredTriangleData:
    def __init__(
        self, *, rgba: tuple[float, float, float, float], triangle_list: np.ndarray
    ):
        assert (
            len(triangle_list.shape) == 2
            and triangle_list.shape[1] == 3
            and triangle_list.dtype == np.float32
        )
        assert len(rgba) == 4
        assert triangle_list.shape[0] > 0
        self.rgba = tuple(rgba)
        self.triangle_list = triangle_list

    @staticmethod
    def square(
        *,
        rgba: tuple[float, float, float, float],
        origin: Iterable[float],
        d1: Iterable[float],
        d2: Iterable[float],
    ) -> "ColoredTriangleData":
        origin = np.array(origin, dtype=np.float32)
        d1 = np.array(d1, dtype=np.float32)
        d2 = np.array(d2, dtype=np.float32)
        p1 = origin + d1
        p2 = origin + d2
        return ColoredTriangleData(
            rgba=rgba,
            triangle_list=np.array(
                [
                    origin,
                    p1,
                    p2,
                    p2,
                    p1,
                    p1 + d2,
                ],
                dtype=np.float32,
            ),
        )

    @staticmethod
    def fused(data: Iterable["ColoredTriangleData"]) -> list["ColoredTriangleData"]:
        groups = collections.defaultdict(list)
        for e in data:
            groups[e.rgba].append(e)
        result = []
        for rgba, group in groups.items():
            if len(group) == 1:
                result.append(group[0])
            else:
                result.append(
                    ColoredTriangleData(
                        rgba=rgba,
                        triangle_list=np.concatenate(
                            [e.triangle_list for e in group], axis=0
                        ),
                    )
                )
        return result


class ColoredLineData:
    def __init__(
        self, *, rgba: tuple[float, float, float, float], edge_list: np.ndarray
    ):
        assert (
            len(edge_list.shape) == 2
            and edge_list.shape[1] == 3
            and edge_list.dtype == np.float32
        )
        assert len(rgba) == 4
        assert edge_list.shape[0] > 0
        self.rgba = tuple(rgba)
        self.edge_list = edge_list

    @staticmethod
    def fused(data: Iterable["ColoredLineData"]) -> list["ColoredLineData"]:
        groups = collections.defaultdict(list)
        for e in data:
            groups[e.rgba].append(e)
        result = []
        for rgba, group in groups.items():
            if len(group) == 1:
                result.append(group[0])
            else:
                result.append(
                    ColoredLineData(
                        rgba=rgba,
                        edge_list=np.concatenate([e.edge_list for e in group], axis=0),
                    )
                )
        return result


def gltf_model_from_colored_triangle_data(
    colored_triangle_data: list[ColoredTriangleData],
    *,
    colored_line_data: Sequence[ColoredLineData] = (),
) -> pygltflib.GLTF2:
    colored_triangle_data = ColoredTriangleData.fused(colored_triangle_data)
    colored_line_data = ColoredLineData.fused(colored_line_data)

    gltf = pygltflib.GLTF2()
    gltf.asset = None

    material_INDICES = {}
    for data in colored_triangle_data:
        material = pygltflib.Material()
        material.pbrMetallicRoughness = pygltflib.PbrMetallicRoughness()
        material.pbrMetallicRoughness.baseColorFactor = data.rgba
        material.pbrMetallicRoughness.roughnessFactor = 0.8
        material.pbrMetallicRoughness.metallicFactor = 0.3
        material.emissiveFactor = None
        material.alphaMode = None
        material.alphaCutoff = None
        material.doubleSided = True
        material_INDICES[data.rgba] = len(gltf.materials)
        gltf.materials.append(material)
    for data in colored_line_data:
        material = pygltflib.Material()
        material.pbrMetallicRoughness = pygltflib.PbrMetallicRoughness()
        material.pbrMetallicRoughness.baseColorFactor = data.rgba
        material.pbrMetallicRoughness.roughnessFactor = 0.8
        material.pbrMetallicRoughness.metallicFactor = 0.3
        material.emissiveFactor = None
        material.alphaMode = None
        material.alphaCutoff = None
        material_INDICES[data.rgba] = len(gltf.materials)
        gltf.materials.append(material)

    shared_buffer = pygltflib.Buffer()
    coords_tri = (
        np.array([])
        if not colored_triangle_data
        else np.concatenate(
            [data.triangle_list for data in colored_triangle_data], axis=0
        )
    )
    coords_edg = (
        np.array([])
        if not colored_line_data
        else np.concatenate([data.edge_list for data in colored_line_data], axis=0)
    )
    coord_data = coords_tri.tobytes() + coords_edg.tobytes()
    buffer_bytes = base64.b64encode(coord_data).decode()
    shared_buffer.uri = f"data:application/octet-stream;base64,{buffer_bytes}"
    shared_buffer.byteLength = len(buffer_bytes)
    shared_buffer_INDEX = len(gltf.buffers)
    gltf.buffers.append(shared_buffer)

    buffer_view_INDICES = {}
    byte_offset = 0
    for data in colored_triangle_data:
        bufferView = pygltflib.BufferView()
        bufferView.buffer = shared_buffer_INDEX
        byte_length = data.triangle_list.shape[0] * 3 * 4
        bufferView.byteOffset = byte_offset
        bufferView.byteLength = byte_length
        byte_offset += byte_length
        bufferView.target = pygltflib.ARRAY_BUFFER
        buffer_view_INDICES[data.rgba] = len(gltf.bufferViews)
        gltf.bufferViews.append(bufferView)
    for data in colored_line_data:
        bufferView = pygltflib.BufferView()
        bufferView.buffer = shared_buffer_INDEX
        byte_length = data.edge_list.shape[0] * 3 * 4
        bufferView.byteOffset = byte_offset
        bufferView.byteLength = byte_length
        byte_offset += byte_length
        bufferView.target = pygltflib.ARRAY_BUFFER
        buffer_view_INDICES[data.rgba] = len(gltf.bufferViews)
        gltf.bufferViews.append(bufferView)

    accessor_INDICES = {}
    for data in colored_triangle_data:
        accessor = pygltflib.Accessor()
        accessor.bufferView = buffer_view_INDICES[data.rgba]
        accessor.byteOffset = 0
        accessor.componentType = pygltflib.FLOAT
        accessor.count = data.triangle_list.shape[0]
        accessor.type = pygltflib.VEC3
        accessor.max = [float(e) for e in np.max(data.triangle_list, axis=0)]
        accessor.min = [float(e) for e in np.min(data.triangle_list, axis=0)]
        accessor_INDICES[data.rgba] = len(gltf.accessors)
        gltf.accessors.append(accessor)
    for data in colored_line_data:
        accessor = pygltflib.Accessor()
        accessor.bufferView = buffer_view_INDICES[data.rgba]
        accessor.byteOffset = 0
        accessor.componentType = pygltflib.FLOAT
        accessor.count = data.edge_list.shape[0]
        accessor.type = pygltflib.VEC3
        accessor.max = [float(e) for e in np.max(data.edge_list, axis=0)]
        accessor.min = [float(e) for e in np.min(data.edge_list, axis=0)]
        accessor_INDICES[data.rgba] = len(gltf.accessors)
        gltf.accessors.append(accessor)

    mesh0 = pygltflib.Mesh()
    for data in colored_triangle_data:
        primitive = pygltflib.Primitive()
        primitive.material = material_INDICES[data.rgba]
        primitive.attributes.POSITION = accessor_INDICES[data.rgba]
        primitive.mode = pygltflib.TRIANGLES
        mesh0.primitives.append(primitive)
    for data in colored_line_data:
        primitive = pygltflib.Primitive()
        primitive.material = material_INDICES[data.rgba]
        primitive.attributes.POSITION = accessor_INDICES[data.rgba]
        primitive.mode = pygltflib.LINES
        mesh0.primitives.append(primitive)
    mesh0_INDEX = len(gltf.meshes)
    gltf.meshes.append(mesh0)

    node0 = pygltflib.Node()
    node0.mesh = mesh0_INDEX
    node0_INDEX = len(gltf.nodes)
    gltf.nodes.append(node0)

    scene = pygltflib.Scene()
    scene.nodes = [node0_INDEX]
    gltf.scenes.append(scene)

    return gltf


def viz_3d_gltf_model_html(model: pygltflib.GLTF2) -> str:
    model_bytes = b"".join(model.save_to_bytes())

    model_data_uri = (
        f"""data:text/plain;base64,{base64.b64encode(model_bytes).decode()}"""
    )

    return (
        r'''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
</head>
<body>
  <a download="model.gltf" id="stim-3d-viewer-download-link" href="'''
        + model_data_uri
        + r"""">Download 3D Model as .GLTF File</a>
  <br>Mouse Wheel = Zoom. Left Drag = Orbit. Right Drag = Strafe.
  <div style="border: 1px dashed gray; margin-bottom: 50px; width: 100%; height: 600px; resize: both; overflow: hidden">
    <div id="stim-3d-viewer-scene-container" style="width: 100%; height: 100%;">JavaScript Blocked?</div>
  </div>

  <script type="module">
    /// BEGIN TERRIBLE HACK.
    /// Get the object by ID then change the ID.
    /// This is a workaround for https://github.com/jupyter/notebook/issues/6598
    let container = document.getElementById("stim-3d-viewer-scene-container");
    container.id = "stim-3d-viewer-scene-container-USED";
    let downloadLink = document.getElementById("stim-3d-viewer-download-link");
    downloadLink.id = "stim-3d-viewer-download-link-USED";
    /// END TERRIBLE HACK.

    container.textContent = "Loading viewer...";

    /// BEGIN TERRIBLE HACK.
    /// This a workaround for https://github.com/jupyter/notebook/issues/6597
    ///
    /// What this SHOULD be is:
    ///
    /// import {Box3, Scene, Color, PerspectiveCamera, WebGLRenderer, DirectionalLight} from "three";
    /// import {OrbitControls} from "three-orbitcontrols";
    /// import {GLTFLoader} from "three-gltf-loader";
    ///
    /// assuming the following import map exists:
    ///
    /// with import map:
    ///   {
    ///     "imports": {
    ///       "three": "https://unpkg.com/three@0.138.0/build/three.module.js",
    ///       "three-orbitcontrols": "https://unpkg.com/three@0.138.0/examples/jsm/controls/OrbitControls.js",
    ///       "three-gltf-loader": "https://unpkg.com/three@0.138.0/examples/jsm/loaders/GLTFLoader.js"
    ///     }
    ///   }
    import {
        AmbientLight,WebGLRenderer,Scene,EventDispatcher,MOUSE,Quaternion,Spherical,TOUCH,Vector2,Vector3,AnimationClip,Bone,Box3,BufferAttribute,BufferGeometry,ClampToEdgeWrapping,Color,DirectionalLight,DoubleSide,FileLoader,FrontSide,Group,ImageBitmapLoader,InterleavedBuffer,InterleavedBufferAttribute,Interpolant,InterpolateDiscrete,InterpolateLinear,Line,LineBasicMaterial,LineLoop,LineSegments,LinearFilter,LinearMipmapLinearFilter,LinearMipmapNearestFilter,Loader,LoaderUtils,Material,MathUtils,Matrix4,Mesh,MeshBasicMaterial,MeshPhysicalMaterial,MeshStandardMaterial,MirroredRepeatWrapping,NearestFilter,NearestMipmapLinearFilter,NearestMipmapNearestFilter,NumberKeyframeTrack,Object3D,OrthographicCamera,PerspectiveCamera,PointLight,Points,PointsMaterial,PropertyBinding,QuaternionKeyframeTrack,RepeatWrapping,Skeleton,SkinnedMesh,Sphere,SpotLight,TangentSpaceNormalMap,Texture,TextureLoader,TriangleFanDrawMode,TriangleStripDrawMode,VectorKeyframeTrack,sRGBEncoding
    } from "https://unpkg.com/three@0.138.0/build/three.module.js";
    async function workaround(result, url) {
        let fetched = await fetch(url);
        let content = await (await fetched.blob()).text();
        let strip_module = content.split("} from 'three';")[1].split("export {")[0];
        let wrap_function = "(() => {" + strip_module + "\nreturn " + result + ";\n})()";
        return eval(wrap_function);
    }
    let OrbitControls = await workaround("OrbitControls", "https://unpkg.com/three@0.138.0/examples/jsm/controls/OrbitControls.js");
    let GLTFLoader = await workaround("GLTFLoader", "https://unpkg.com/three@0.138.0/examples/jsm/loaders/GLTFLoader.js");
    ///
    /// END TERRIBLE HACK.
    ///

    try {
      container.textContent = "Loading model...";
      let modelDataUri = downloadLink.href;
      let gltf = await new GLTFLoader().loadAsync(modelDataUri);
      container.textContent = "Loading scene...";

      // Create the scene, adding lighting for the loaded objects.
      let scene = new Scene();
      scene.background = new Color("white");
      let mainLight = new DirectionalLight(0xffffff, 5);
      mainLight.position.set(1, 2, 3);
      let backLight = new DirectionalLight(0xffffff, 4);
      backLight.position.set(-1, -2, -4);
      let ambientLight =  new AmbientLight(0xffffff, 1);
      scene.add(mainLight);
      scene.add(backLight);
      scene.add(ambientLight);
      scene.add(gltf.scene);

      // Point the camera at the center, far enough back to see everything.
      let camera = new PerspectiveCamera(35, container.clientWidth / container.clientHeight, 0.1, 100000);
      let controls = new OrbitControls(camera, container);
      let bounds = new Box3().setFromObject(scene);
      let mid = new Vector3(
          (bounds.min.x + bounds.max.x) * 0.5,
          (bounds.min.y + bounds.max.y) * 0.5,
          (bounds.min.z + bounds.max.z) * 0.5,
      );
      let boxPoints = [];
      for (let dx of [0, 0.5, 1]) {
          for (let dy of [0, 0.5, 1]) {
              for (let dz of [0, 0.5, 1]) {
                  boxPoints.push(new Vector3(
                      bounds.min.x + (bounds.max.x - bounds.min.x) * dx,
                      bounds.min.y + (bounds.max.y - bounds.min.y) * dy,
                      bounds.min.z + (bounds.max.z - bounds.min.z) * dz,
                  ));
              }
          }
      }
      let isInView = p => {
          p = new Vector3(p.x, p.y, p.z);
          p.project(camera);
          return Math.abs(p.x) < 1 && Math.abs(p.y) < 1 && p.z >= 0 && p.z < 1;
      };
      let unit = new Vector3(0.3, 0.4, -1.8);
      unit.normalize();
      let setCameraDistance = d => {
          controls.target.copy(mid);
          camera.position.copy(mid);
          camera.position.addScaledVector(unit, d);
          controls.update();
          return boxPoints.every(isInView);
      };

      let maxDistance = 1;
      for (let k = 0; k < 20; k++) {
          if (setCameraDistance(maxDistance)) {
              break;
          }
          maxDistance *= 2;
      }
      let minDistance = maxDistance;
      for (let k = 0; k < 20; k++) {
          minDistance /= 2;
          if (!setCameraDistance(minDistance)) {
              break;
          }
      }
      for (let k = 0; k < 20; k++) {
          let mid = (minDistance + maxDistance) / 2;
          if (setCameraDistance(mid)) {
              maxDistance = mid;
          } else {
              minDistance = mid;
          }
      }
      setCameraDistance(maxDistance);

      // Set up rendering.
      let renderer = new WebGLRenderer({ antialias: true });
      container.textContent = "";
      renderer.setSize(container.clientWidth, container.clientHeight);
      renderer.setPixelRatio(window.devicePixelRatio);
      renderer.physicallyCorrectLights = true;
      container.appendChild(renderer.domElement);

      // Render whenever any important changes have occurred.
      requestAnimationFrame(() => renderer.render(scene, camera));
      new ResizeObserver(() => {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.render(scene, camera);
      }).observe(container);
      controls.addEventListener("change", () => {
          renderer.render(scene, camera);
      })
    } catch (ex) {
      container.textContent = "Failed to show model. " + ex;
      console.error(ex);
    }
  </script>
</body>
    """
    )
