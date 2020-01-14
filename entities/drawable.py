# -*- coding: utf-8 -*-

import abc
import pygame


class Drawable(abc.ABC):
    """ Abstract drawable class. Implements a generic object that can be
    painted in the screen.
    """
    def __init__(self,
                 screen: pygame.Surface,
                 color: pygame.Color = None,
                 border_color: pygame.Color = None,
                 border_size: pygame.Color = None):
        self.screen = screen  # screen to paint to
        self.color = color
        self.border_color = border_color
        self.border_size = border_size

    def draw(self):
        if self.color is None or self.border_color is None:
            return

        if self.border_size is None:
            return

        r = self.rect
        if r is None:
            return

        pygame.draw.rect(self.screen, self.color, r, 0)
        pygame.draw.rect(self.screen, self.border_color, r, self.border_size)

    @property
    @abc.abstractmethod
    def rect(self) -> pygame.Rect or None:
        """ Must be overloaded by children classes
        """
        return None
