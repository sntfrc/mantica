import { useEffect, useRef, useState } from 'react';
import { Animated, Button, Easing, ImageBackground, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { CameraView, CameraType, useCameraPermissions, Camera } from 'expo-camera';
import { manipulateAsync, FlipType, SaveFormat } from 'expo-image-manipulator';

import Ionicons from '@expo/vector-icons/Ionicons';
import MaterialCommunityIcons from '@expo/vector-icons/MaterialCommunityIcons';

import i18n from './translations';

export default function App() {
  const [facing, setFacing] = useState<CameraType>('back');

  const [state, setState] = useState({
    lock: false,
    review: false,
    error: false,
  });
  
  const [picture, setPicture] = useState<string>("");

  const [permission, requestPermission] = useCameraPermissions();

  const camera = useRef<CameraView>(null);
  const still = useRef<View>(null);

  if (!permission) {
    return <View/>
  }

  if (!permission.granted) {
    requestPermission();
  }

  function toggleCameraFacing() {
    setFacing(current => (current === 'back' ? 'front' : 'back'));
  }

  function takePicture() {
    camera.current?.takePictureAsync().then(async (res) => {
      if (res && res.base64) {
        var pic = null;
        if (facing === "front") {
          let fixed = await manipulateAsync(res.base64,
            [{ rotate: 180 }, { flip: FlipType.Vertical }],
            { compress: 1, format: SaveFormat.PNG }
          );
          pic = fixed.uri;
        } else {
          pic = res.base64;
        }
        setPicture(pic);
        setState((ps) => ({...ps, lock: true}));
        try {
          return generate(pic);
        } catch (e) {
          console.log(e);
          return new Promise(x => null);
        }
      } else {
        return new Promise(x => null);
      }
    }).then((data) => {
      if (data) {
        setPicture(data as string);
        setState((ps) => ({...ps, review: true}));
      } else {
        setState((ps) => ({...ps, error: true}));
      }
    });
  }

  function keepPicture() {
    fetch(picture).then((x) => {
      return x.blob();
    }).then((x) => {
      const file = new File([x], 'MadeWithMantica.png', { type: x.type });
      navigator.share({ files: [file] });
    });
  }

  function backToCamera() {
    setState((ps) => ({lock: false, review: false, error: false}));
  }

  async function generate(picture: string) {
    var getString = 'generate.php?dream=85';
    console.log(picture);
    const response = await fetch(getString, {
        method: 'POST',
        headers: {
            'Content-Type': 'text/octet-stream'
        },
        body: picture
    });

    if (response.ok) {
        var genData = await response.json();
        return convertImageToDataUri(genData.image);
    } else {
        console.error('Failed to send photo:', response.statusText);
        return null;
    }
  }

  async function convertImageToDataUri(url: string) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error('Failed to fetch image: ${response.statusText}');
    }
    const blob = await response.blob();
    return await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
  }
  
  return (
    <View style={styles.container}>
      {!state.lock &&
        <CameraView ref={camera} style={styles.camera} facing={facing} mirror={true}>
          <View style={styles.buttonContainer}>

            <View style={styles.button}></View>

            <View style={styles.button}>
              <TouchableOpacity style={styles.iconShot} onPress={takePicture}>
                <Ionicons name="aperture" size={80} color="#800080" />
              </TouchableOpacity>
            </View>

            <View style={styles.button}>
              <TouchableOpacity style={styles.iconSmall} onPress={toggleCameraFacing}>
                <Ionicons name="camera-reverse" size={30} color="#ffffff80" />
              </TouchableOpacity>
            </View>
          </View>
        </CameraView>
      }

      {state.lock && 
        <Animated.View style={[styles.camera, (!state.review && !state.error) && styles.overlay]}>
          <ImageBackground style={styles.camera} source={{uri: picture}} resizeMode="cover">
            {state.error && 
              <View style={styles.error}>
                <MaterialCommunityIcons name="wifi-off" size={200} color="#ffffff80" />
              </View>
            }
            <View style={styles.buttonContainer}>

              <View style={styles.button}>
                {state.review && <TouchableOpacity style={styles.iconSmallFull} onPress={keepPicture}>
                  <Ionicons name="share" size={30} color="#ffffff" />
                </TouchableOpacity>}
              </View>

              <View style={styles.button}></View>

              <View style={styles.button}>
                {(state.review || state.error) && <TouchableOpacity style={styles.iconSmallFull} onPress={backToCamera}>
                  <Ionicons name="refresh" size={30} color="#ffffff" />
                </TouchableOpacity>}
              </View>
            </View>
          </ImageBackground>
        </Animated.View>
      }
    </View>
  );
}

const opacity = useRef(new Animated.Value(1.0)).current;
const animateOpacity =  Animated.loop(Animated.sequence([
    Animated.timing(opacity, {toValue: 0.5, duration: 500, easing: Easing.in(Easing.sin), useNativeDriver: true}),
    Animated.timing(opacity, {toValue: 1.0, duration: 500, easing: Easing.inOut(Easing.sin), useNativeDriver: true})
]));
animateOpacity.start();

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#222222',
    justifyContent: 'center',
  },
  permission: {
    textAlign: 'center',
    paddingBottom: 30,
    color: 'white'
  },
  buttonPerm: {
    marginLeft: 'auto',
    marginRight: 'auto'
  },
  camera: {
    flex: 1,
  },
  overlay: {
    opacity: opacity
  },
  error: {
    flex: 3,
    justifyContent: 'center',
    alignItems: 'center'
  },
  buttonContainer: {
    flex: 1,
    flexDirection: 'row',
    margin: 0,
    marginBottom: 32,
    alignItems: 'center',
    backgroundColor: 'transparent'
  },
  button: {
    flex: 1,
    alignSelf: 'flex-end',
    alignItems: 'center'
  },
  iconShot: {
    borderRadius: 50,
    backgroundColor: '#80008080'
  },
  iconSmall: {
    padding: 20,
  },
  iconSmallFull: {
    padding: 20,
    borderRadius: 100,
    backgroundColor: '#200020d0'
  }
});
