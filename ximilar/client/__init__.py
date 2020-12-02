from .client import RestClient
from .recognition import RecognitionClient
from .tagging import GenericTaggingClient, FashionTaggingClient
from .colors import DominantColorProductClient, DominantColorGenericClient
from .visual import VisualSearchClient
from .detection import DetectionClient
from .search import SimilarityPhotosClient, SimilarityProductsClient, SimilarityFashionClient, SimilarityCustomClient
from .flows import FlowsClient
from .exceptions import XimilarClientException
