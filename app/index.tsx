import { useRef, useState } from 'react';
import { Button, Easing, ImageBackground, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import { manipulateAsync, FlipType, SaveFormat } from 'expo-image-manipulator';

import Ionicons from '@expo/vector-icons/Ionicons';

import i18n from './translations';

export default function App() {
  const [facing, setFacing] = useState<CameraType>('back');
  const [lock, setLock] = useState<boolean>(false);
  const [review, setReview] = useState<boolean>(false);
  
  const [picture, setPicture] = useState<string>("");

  const [permission, requestPermission] = useCameraPermissions();

  const camera = useRef<CameraView>(null);
  const still = useRef<View>(null);

  if (!permission) {
    return <View />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.permission}>{i18n.t('permission')}</Text>
        <Button onPress={requestPermission} title={i18n.t('grant')} />
      </View>
    );
  }

  function toggleCameraFacing() {
    setFacing(current => (current === 'back' ? 'front' : 'back'));
  }

  function takePicture() {
    camera.current?.takePictureAsync().then(async (res) => {
      if (res && res.base64) {
        if (facing === "front") {
          let fixed = await manipulateAsync(res.base64,
            [{ rotate: 180 }, { flip: FlipType.Vertical }],
            { compress: 1, format: SaveFormat.PNG }
          );
          setPicture(fixed.uri);
        } else {
          setPicture(res.base64);
        }
        setLock(true);
        return new Promise(x => setTimeout(x, 4000));
      } else {
        return new Promise(x => null);
      }
    }).then((data) => {
      setReview(true);
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
    setReview(false);
    setLock(false);
  }

  return (
    <View style={styles.container}>
      {!lock && <CameraView ref={camera} style={styles.camera} facing={facing} mirror={true}>
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
      </CameraView>}

      {lock && <ImageBackground style={styles.camera} source={{ uri: picture }} resizeMode="cover">
        <View style={styles.buttonContainer}>

          <View style={styles.button}>
            {review && <TouchableOpacity style={styles.iconSmallFull} onPress={keepPicture}>
              <Ionicons name="share" size={30} color="#ffffff" />
            </TouchableOpacity>}
          </View>

          <View style={styles.button}></View>

          <View style={styles.button}>
            {review && <TouchableOpacity style={styles.iconSmallFull} onPress={backToCamera}>
              <Ionicons name="refresh" size={30} color="#ffffff" />
            </TouchableOpacity>}
          </View>
        </View>
      </ImageBackground>}
    </View>
  );
}

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

  camera: {
    flex: 1,
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
