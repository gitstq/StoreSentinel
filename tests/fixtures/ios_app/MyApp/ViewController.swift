import UIKit
import AVFoundation

class ViewController: UIViewController {
    let manager = CLLocationManager()

    override func viewDidLoad() {
        super.viewDidLoad()
        manager.requestWhenInUseAuthorization()
        let session = AVCaptureSession()
        // uses camera for QR scanning
        print(session, "cameraCaptureOutput placeholder")
    }
}
