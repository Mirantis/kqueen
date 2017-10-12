
function topology_data_transform(clusterData) {

  // Basic Transformation Array > Object with UID as Keys
  const transformedData = clusterData.items.reduce(function(acc, cur) {
    acc[cur.metadata.uid] = cur
    return acc
  }, {})

  // Add Containers as top-level resource
  let resource
  for (resource in transformedData) {
    resource = transformedData[resource]
    if (resource.kind === 'Pod') {
      for (container of resource.spec.containers) {
        let containerId = `${resource.metadata.uid}-${container.name}`
        transformedData[containerId] = { }
        transformedData[containerId].metadata = container
        transformedData[containerId].kind = 'Container'

        // Add to relations
        relations.push({ target: containerId, source: resource.metadata.uid })
      }
    }
  }

  let item, kind

  for (item of clusterData.items) {
    kind = item.kind
    if (kind === 'Pod') {
      let pod = item
      // define relationship between pods and nodes
      let podsNode = clusterData.items.find(i => i.metadata.name === pod.spec.nodeName)
      relations.push({source: pod.metadata.uid, target: podsNode.metadata.uid})

      // define relationships between pods and rep sets and replication controllers
      let ownerReferences = pod.metadata.ownerReferences[0].uid
      let podsRepController = clusterData.items.find(i => i.metadata.uid === ownerReferences)
      relations.push({target: pod.metadata.uid, source: podsRepController.metadata.uid})


      // rel'n between pods and services
      let podsService = clusterData.items.find(i => {
        if (i.kind === 'Service' && i.spec.selector) {
          return i.spec.selector.run === pod.metadata.labels.run
        }
      })
      relations.push({target: pod.metadata.uid, source: podsService.metadata.uid})
    }

    if (kind === 'Service') {
      let podsService
      // console.log('item', item)
      // console.log(item.spec.selector)
    }

    if (kind === 'Deployment') {
      // console.log('item deployment', item)
    }
  }

  const items = transformedData
  return {items: items, relations: relations}
}
