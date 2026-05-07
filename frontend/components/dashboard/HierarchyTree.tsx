"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

export interface HierarchyStore {
  id: string;
  raw_name: string;
  display_name: string | null;
  country: string | null;
  state: string | null;
  city: string | null;
  locality: string | null;
  store_type: string | null;
  parse_confidence: number | null;
  detected_chain?: string | null;
}

interface HierarchyTreeProps {
  stores: HierarchyStore[];
  selectedStoreId?: string | null;
  onSelectStore?: (storeId: string) => void;
}

interface TreeNode {
  key: string;
  label: string;
  storeCount: number;
  children: TreeNode[];
  storeIds: string[];
}

const UNKNOWN = "Unknown";

function groupBy<T>(items: T[], key: (item: T) => string): Map<string, T[]> {
  const map = new Map<string, T[]>();
  for (const item of items) {
    const k = key(item);
    const existing = map.get(k);
    if (existing) {
      existing.push(item);
    } else {
      map.set(k, [item]);
    }
  }
  return map;
}

function buildTree(stores: HierarchyStore[]): TreeNode[] {
  const byCountry = groupBy(stores, (store) => (store.country || "India").trim() || "India");
  const tree: TreeNode[] = [];

  for (const [country, countryStores] of byCountry) {
    const stateNodes: TreeNode[] = [];
    const byState = groupBy(countryStores, (store) => (store.state || `${UNKNOWN} state`).trim());

    for (const [state, stateStores] of byState) {
      const cityNodes: TreeNode[] = [];
      const byCity = groupBy(stateStores, (store) => (store.city || `${UNKNOWN} city`).trim());

      for (const [city, cityStores] of byCity) {
        const localityNodes: TreeNode[] = [];
        const byLocality = groupBy(cityStores, (store) => (store.locality || "").trim());

        for (const [locality, localStores] of byLocality) {
          if (locality.length === 0) {
            // No locality — attach stores directly under city, no extra node
            continue;
          }
          localityNodes.push({
            key: `${country}|${state}|${city}|${locality}`,
            label: locality,
            storeCount: localStores.length,
            children: [],
            storeIds: localStores.map((store) => store.id),
          });
        }

        // Stores in this city without a locality go straight under the city node
        const directStores = cityStores
          .filter((store) => !(store.locality && store.locality.trim()))
          .map((store) => store.id);

        cityNodes.push({
          key: `${country}|${state}|${city}`,
          label: city,
          storeCount: cityStores.length,
          children: localityNodes.sort((a, b) => a.label.localeCompare(b.label)),
          storeIds: directStores,
        });
      }

      stateNodes.push({
        key: `${country}|${state}`,
        label: state,
        storeCount: stateStores.length,
        children: cityNodes.sort((a, b) => a.label.localeCompare(b.label)),
        storeIds: [],
      });
    }

    tree.push({
      key: country,
      label: country,
      storeCount: countryStores.length,
      children: stateNodes.sort((a, b) => a.label.localeCompare(b.label)),
      storeIds: [],
    });
  }

  return tree.sort((a, b) => a.label.localeCompare(b.label));
}

interface NodeRowProps {
  node: TreeNode;
  depth: number;
  storesById: Map<string, HierarchyStore>;
  expanded: Set<string>;
  toggle: (key: string) => void;
  selectedStoreId?: string | null;
  onSelectStore?: (storeId: string) => void;
}

function StoreLeafRow({
  store,
  depth,
  selected,
  onClick,
}: {
  store: HierarchyStore;
  depth: number;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-left text-sm transition ${
        selected ? "bg-pine/10 text-ink" : "text-ink/80 hover:bg-canvas/60"
      }`}
      style={{ paddingLeft: depth * 16 + 24 }}
    >
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{store.display_name ?? store.raw_name}</p>
        <p className="truncate text-[10px] uppercase tracking-wider text-ink/40">
          {[store.locality, store.city, store.store_type].filter(Boolean).join(" · ") || "Store"}
        </p>
      </div>
      <span className="ml-2 shrink-0 text-[10px] font-mono text-ink/40">
        {store.parse_confidence !== null && store.parse_confidence !== undefined
          ? `${Math.round((store.parse_confidence || 0) * 100)}%`
          : ""}
      </span>
    </button>
  );
}

function NodeRow({
  node,
  depth,
  storesById,
  expanded,
  toggle,
  selectedStoreId,
  onSelectStore,
}: NodeRowProps) {
  const isOpen = expanded.has(node.key);
  const hasChildren = node.children.length > 0 || node.storeIds.length > 0;

  return (
    <div>
      <button
        type="button"
        onClick={() => toggle(node.key)}
        className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm font-semibold text-ink transition hover:bg-canvas/60"
        style={{ paddingLeft: depth * 16 + 4 }}
      >
        <span className={`inline-block w-3 text-center text-ink/50 transition ${isOpen ? "rotate-90" : ""}`}>
          {hasChildren ? "›" : "·"}
        </span>
        <span className="flex-1">{node.label}</span>
        <span className="text-[11px] font-mono text-ink/50">{node.storeCount}</span>
      </button>

      {isOpen ? (
        <div className="mt-0.5">
          {node.children.map((child) => (
            <NodeRow
              key={child.key}
              node={child}
              depth={depth + 1}
              storesById={storesById}
              expanded={expanded}
              toggle={toggle}
              selectedStoreId={selectedStoreId}
              onSelectStore={onSelectStore}
            />
          ))}
          {node.storeIds.map((storeId) => {
            const store = storesById.get(storeId);
            if (!store) return null;
            return (
              <StoreLeafRow
                key={storeId}
                store={store}
                depth={depth + 1}
                selected={selectedStoreId === storeId}
                onClick={() => onSelectStore?.(storeId)}
              />
            );
          })}
        </div>
      ) : null}
    </div>
  );
}

export default function HierarchyTree({
  stores,
  selectedStoreId,
  onSelectStore,
}: HierarchyTreeProps) {
  const router = useRouter();
  const tree = useMemo(() => buildTree(stores), [stores]);
  const storesById = useMemo(() => {
    const map = new Map<string, HierarchyStore>();
    for (const store of stores) {
      map.set(store.id, store);
    }
    return map;
  }, [stores]);

  const [expanded, setExpanded] = useState<Set<string>>(() => {
    const initial = new Set<string>();
    // Default-expand the first country and its states
    if (tree.length > 0) {
      initial.add(tree[0].key);
      for (const stateNode of tree[0].children) {
        initial.add(stateNode.key);
      }
    }
    return initial;
  });

  const toggle = (key: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });

  const handleSelectStore = (storeId: string) => {
    if (onSelectStore) {
      onSelectStore(storeId);
    } else {
      router.push(`/stores/${storeId}`);
    }
  };

  if (stores.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-ink/20 bg-white/60 p-6 text-center text-sm text-ink/60">
        <p>No stores yet.</p>
        <button
          type="button"
          onClick={() => router.push("/upload")}
          className="mt-3 rounded-full bg-pine px-3 py-1.5 text-xs font-semibold text-white"
        >
          Upload stores
        </button>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-ink/10 bg-white p-3 shadow-sm">
      <div className="space-y-0.5">
        {tree.map((node) => (
          <NodeRow
            key={node.key}
            node={node}
            depth={0}
            storesById={storesById}
            expanded={expanded}
            toggle={toggle}
            selectedStoreId={selectedStoreId}
            onSelectStore={handleSelectStore}
          />
        ))}
      </div>
    </div>
  );
}
