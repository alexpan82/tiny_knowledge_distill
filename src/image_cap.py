import torch.nn as nn

from encoder import Encoder
from decoder import Decoder
from collections import OrderedDict 

class ImageCap(nn.Module):
    """
        Combine encoder.py and decoder.py into a fully functioning image-captioning model
    """
    def __init__(self, hidden_dim=768, max_outseq_len=50, num_beams=5):
        super(ImageCap, self).__init__()

        self.hidden_dim = hidden_dim
        self.max_outseq_len = max_outseq_len
        self.num_beams = num_beams

        self.encoder_model = Encoder(hidden_dim=self.hidden_dim)

        # NOTE: magic number which is 7*7*hidden_dim, where 7*7 is the last
        # window size of TinyViT
        self.projection_layer = nn.Linear(37632, hidden_dim)

        self.decoder_model = Decoder(hidden_dim=self.hidden_dim,
                                     max_outseq_len=self.max_outseq_len,
                                     num_beams=self.num_beams)
        
        self.decoder_out = OrderedDict()
        # Hook last 2 layers to save decoder output hidden state and lm_head to self.decoder_out
        self.decoder_model.model.transformer.register_forward_hook(self.forward_hook('decoder_out_hidden'))
        self.decoder_model.model.lm_head.register_forward_hook(self.forward_hook('decoder_out_head'))

        
    def forward(self, X):
        """ 
        Encoder output shape from TinyViT doesn't match what's expected by decoder by default
        This is because TinyViT was originally an image classification model
        
        At the end of the attention modules, TinyViT performs an average over all hidden states
        to produce a single hidden state that is then used for classification
        
        To prevent this averaging over hidden states,
        line 578 of models/TinyViT/models/tiny_vit.py was commented out
        """
        encoder_out = self.encoder_model.forward(X)
        projection = self.projection_layer(encoder_out.flatten(start_dim=1))
        decoder_out = self.decoder_model.forward(projection)
        return decoder_out
    
    def forward_hook(self, layer_name):
        def hook(module, input, output):
            self.decoder_out[layer_name] = output[0]
        return hook

    
if __name__ == "__main__":
    model = ImageCap()
    print(f"{model=}")
