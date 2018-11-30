//
//  ViewController.swift
//  TensorCoreml
//
//  Created by Anusha Godavarthi on 11/14/18.
//  Copyright © 2018 Anusha Godavarthi. All rights reserved.
//

import UIKit

class ViewController: UIViewController {
    
    @IBOutlet weak var pictureImageView :UIImageView!
    @IBOutlet weak var titleLabel :UILabel!
    
    private var model :inceptionV1 = inceptionV1()

    let images = ["cat.jpg","dog.jpg","rat.jpg","banana.jpg"]
    var index = 0
    
    override func viewDidLoad() {
        super.viewDidLoad()
        // Do any additional setup after loading the view, typically from a nib.
    }

    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
        // Dispose of any resources that can be recreated.
    }

    @IBAction func nextButtonPressed(){
        
        if index > self.images.count - 1{
            index = 0
        }
        let img = UIImage(named: images[index])
        self.pictureImageView.image = img
        
        let resizedImage = img?.resizeTo(size: CGSize(width: 224, height:224))
        
        let buffer = resizedImage?.toBuffer()
        
        let prediction = try! self.model.prediction(input: inceptionV1Input(input__0: buffer!))
       
        self.titleLabel.text = prediction.classLabel
    
        index = index + 1
    }
}

