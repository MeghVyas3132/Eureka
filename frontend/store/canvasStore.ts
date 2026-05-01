import { create } from "zustand";

export interface Zone {
  id: string;
  layout_id: string;
  name: string;
  zone_type: "aisle" | "entrance" | "checkout" | "department" | "storage" | "other";
  x: number;
  y: number;
  width: number;
  height: number;
  shelves: Shelf[];
}

export interface Shelf {
  id: string;
  zone_id: string;
  x: number;
  y: number;
  width_cm: number;
  height_cm: number;
  num_rows: number;
}

export interface Layout {
  id: string;
  store_id: string;
  name: string;
  created_at: string;
  updated_at: string;
  zones: Zone[];
  versions: LayoutVersionSummary[];
}

export interface LayoutVersionSummary {
  id: string;
  version_number: number;
  created_at: string;
}

interface CanvasStore {
  layout: Layout | null;
  zones: Zone[];
  selectedZoneId: string | null;
  selectedShelfId: string | null;
  isDirty: boolean;

  setLayout: (layout: Layout) => void;
  updateZone: (zone: Zone) => void;
  addZone: (zone: Zone) => void;
  deleteZone: (zoneId: string) => void;
  updateShelf: (shelf: Shelf) => void;
  addShelf: (zoneId: string, shelf: Shelf) => void;
  deleteShelf: (zoneId: string, shelfId: string) => void;
  setSelectedZone: (id: string | null) => void;
  setSelectedShelf: (id: string | null) => void;
  markDirty: () => void;
  markSaved: () => void;
  clearCanvas: () => void;
}

export const useCanvasStore = create<CanvasStore>((set) => ({
  layout: null,
  zones: [],
  selectedZoneId: null,
  selectedShelfId: null,
  isDirty: false,

  setLayout: (layout) => set({ layout, zones: layout.zones, isDirty: false }),

  updateZone: (updatedZone) =>
    set((state) => ({
      zones: state.zones.map((zone) => (zone.id === updatedZone.id ? updatedZone : zone)),
      isDirty: true,
    })),

  addZone: (zone) => set((state) => ({ zones: [...state.zones, zone], isDirty: true })),

  deleteZone: (zoneId) =>
    set((state) => ({
      zones: state.zones.filter((zone) => zone.id !== zoneId),
      selectedZoneId: state.selectedZoneId === zoneId ? null : state.selectedZoneId,
      isDirty: true,
    })),

  updateShelf: (updatedShelf) =>
    set((state) => ({
      zones: state.zones.map((zone) =>
        zone.id === updatedShelf.zone_id
          ? {
              ...zone,
              shelves: zone.shelves.map((shelf) => (shelf.id === updatedShelf.id ? updatedShelf : shelf)),
            }
          : zone,
      ),
      isDirty: true,
    })),

  addShelf: (zoneId, shelf) =>
    set((state) => ({
      zones: state.zones.map((zone) =>
        zone.id === zoneId ? { ...zone, shelves: [...zone.shelves, shelf] } : zone,
      ),
      isDirty: true,
    })),

  deleteShelf: (zoneId, shelfId) =>
    set((state) => ({
      zones: state.zones.map((zone) =>
        zone.id === zoneId
          ? { ...zone, shelves: zone.shelves.filter((shelf) => shelf.id !== shelfId) }
          : zone,
      ),
      isDirty: true,
    })),

  setSelectedZone: (id) => set({ selectedZoneId: id, selectedShelfId: null }),
  setSelectedShelf: (id) => set({ selectedShelfId: id }),
  markDirty: () => set({ isDirty: true }),
  markSaved: () => set({ isDirty: false }),
  clearCanvas: () => set({ layout: null, zones: [], isDirty: false }),
}));
