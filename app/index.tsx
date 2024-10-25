import { useRef, useState } from 'react';
import { Button, Easing, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
//import { VolumeManager } from 'react-native-volume-manager';

import {Animated} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';

import i18n from './translations';

export default function App() {
  const [facing, setFacing] = useState<CameraType>('back');
  const [permission, requestPermission] = useCameraPermissions();
  const camera = useRef<CameraView>(null);

  if (!permission) {
    return <View />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.permission}>{i18n.t("permission")}</Text>
        <Button onPress={requestPermission} title={i18n.t("grant")} />
      </View>
    );
  }

  function toggleCameraFacing() {
    setFacing(current => (current === 'back' ? 'front' : 'back'));
  }

  function takePicture() {
    camera.current?.takePictureAsync().then((res) => {
      console.log(res);
    });
  }

  /*VolumeManager.showNativeVolumeUI({ enabled: true });
  const volumeListener = VolumeManager.addVolumeListener((result) => {
    takePicture();
  });*/

  return (
    <View style={styles.container}>
      <CameraView ref={camera} style={styles.camera} facing={facing} mirror={true}>
        <View style={styles.buttonContainer}>
          <View style={styles.button}></View>

          <TouchableOpacity style={styles.button} onPress={takePicture}><View style={styles.iconShot}>
            <Ionicons name="aperture-outline" size={80} color="#800080" />
          </View></TouchableOpacity>

          <TouchableOpacity style={styles.button} onPress={toggleCameraFacing}><View style={styles.iconFlip}>
              <Ionicons name="camera-reverse" size={30} color="#ffffff80" />
          </View></TouchableOpacity>

        </View>
      </CameraView>
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

  iconFlip: {
    padding: 20
  }
});
